#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

/* Calibre takes the first matching device in /proc/mounts. Snap exposes a
 * second, inaccessible copy under hostfs. Supply a fresh read-only snapshot
 * with only confirmed removable-media duplicates removed. Never translate
 * arbitrary file operations or manufacture a mount that is not in the table.
 * Enabled only for the manager by snapcraft.yaml, not every bundled command. */
struct field { const char *text; size_t size; };
struct mount_line {
    const char *text;
    size_t size;
    struct field source, target, type, options;
};

static bool equal(struct field a, struct field b) {
    return a.size == b.size && memcmp(a.text, b.text, a.size) == 0;
}

static bool prefix(struct field f, const char *p) {
    size_t n = strlen(p);
    return f.size > n && memcmp(f.text, p, n) == 0;
}

static struct field field(const char **cursor, const char *end) {
    while (*cursor < end && (**cursor == ' ' || **cursor == '\t')) ++*cursor;
    const char *start = *cursor;
    while (*cursor < end && **cursor != ' ' && **cursor != '\t' &&
           **cursor != '\n') ++*cursor;
    return (struct field){start, (size_t)(*cursor - start)};
}

static bool redundant(const struct mount_line *line,
                      const struct mount_line *lines, size_t count) {
    const char hostfs[] = "/var/lib/snapd/hostfs";
    if (!prefix(line->source, "/dev/") || !prefix(line->target, hostfs))
        return false;
    struct field target = {line->target.text + sizeof(hostfs) - 1,
                           line->target.size - (sizeof(hostfs) - 1)};
    if (!(prefix(target, "/media/") || prefix(target, "/run/media/") ||
          prefix(target, "/mnt/")) || !line->type.size || !line->options.size)
        return false;
    for (size_t i = 0; i < count; ++i) {
        if (equal(target, lines[i].target) &&
            equal(line->source, lines[i].source) &&
            equal(line->type, lines[i].type) &&
            equal(line->options, lines[i].options)) return true;
    }
    return false;
}

static bool enabled(const char *path, int flags) {
    const char *setting = getenv("CALIBRE_SNAP_FILTER_MOUNTS");
    return setting && strcmp(setting, "1") == 0 &&
        (flags & ~(O_CLOEXEC | O_LARGEFILE | O_NONBLOCK | O_NOCTTY | O_NOFOLLOW)) == O_RDONLY &&
        (strcmp(path, "/proc/mounts") == 0 || strcmp(path, "/proc/self/mounts") == 0);
}

static bool write_all(int fd, const char *text, size_t size) {
    while (size) {
        ssize_t n = write(fd, text, size);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) return false;
        text += n;
        size -= (size_t)n;
    }
    return true;
}

/* Return a replacement descriptor, or -1 to keep the original. Bound memory
 * consumption; on any failure rewind and leave the real proc file in use.
 * The real open happens first, so mount-observe remains necessary. */
static int snapshot(int original, int flags) {
    const size_t limit = 16 * 1024 * 1024;
    size_t capacity = 16384, used = 0, count = 0;
    char *text = malloc(capacity);
    struct mount_line *lines = NULL;
    int temporary = -1, result = -1;
    if (!text) return -1;
    for (;;) {
        if (used == capacity) {
            if (capacity == limit) goto done;
            capacity *= 2;
            char *larger = realloc(text, capacity);
            if (!larger) goto done;
            text = larger;
        }
        ssize_t n = read(original, text + used, capacity - used);
        if (n < 0 && errno == EINTR) continue;
        if (n < 0) goto done;
        if (!n) break;
        used += (size_t)n;
    }
    for (size_t i = 0; i < used; ++i) if (text[i] == '\n') ++count;
    if (used && text[used - 1] != '\n') ++count;
    if (!count || count > 100000) goto done;
    lines = calloc(count, sizeof(*lines));
    if (!lines) goto done;
    const char *cursor = text, *end = text + used;
    for (size_t i = 0; i < count; ++i) {
        const char *newline = memchr(cursor, '\n', (size_t)(end - cursor));
        const char *stop = newline ? newline + 1 : end;
        lines[i].text = cursor;
        lines[i].size = (size_t)(stop - cursor);
        lines[i].source = field(&cursor, stop);
        lines[i].target = field(&cursor, stop);
        lines[i].type = field(&cursor, stop);
        lines[i].options = field(&cursor, stop);
        cursor = stop;
    }
    bool changed = false;
    for (size_t i = 0; i < count; ++i) {
        if (redundant(&lines[i], lines, count)) { changed = true; break; }
    }
    if (!changed) goto done;
    temporary = memfd_create("calibre-mounts", MFD_CLOEXEC | MFD_ALLOW_SEALING);
    if (temporary < 0) goto done;
    for (size_t i = 0; i < count; ++i) {
        if (!redundant(&lines[i], lines, count) &&
            !write_all(temporary, lines[i].text, lines[i].size)) goto done;
    }
    if (fcntl(temporary, F_ADD_SEALS,
              F_SEAL_WRITE | F_SEAL_GROW | F_SEAL_SHRINK | F_SEAL_SEAL) < 0) goto done;
    char path[64];
    snprintf(path, sizeof(path), "/proc/self/fd/%d", temporary);
    int (*real_open)(const char *, int, ...) = dlsym(RTLD_NEXT, "open");
    if (real_open) result = real_open(path, O_RDONLY | (flags & (O_CLOEXEC | O_NONBLOCK)));
done:
    if (temporary >= 0) close(temporary);
    free(lines);
    free(text);
    if (lseek(original, 0, SEEK_SET) < 0 && result >= 0) {
        close(result);
        result = -1;
    }
    return result;
}

static int adapt(int fd, const char *path, int flags) {
    int saved = errno;
    if (fd >= 0 && enabled(path, flags)) {
        int replacement = snapshot(fd, flags);
        if (replacement >= 0) { close(fd); fd = replacement; }
    }
    errno = saved;
    return fd;
}

static bool has_mode(int flags) {
    return (flags & O_CREAT) || (flags & O_TMPFILE) == O_TMPFILE;
}

#define OPEN_WRAPPER(name) \
int name(const char *path, int flags, ...) { \
    mode_t mode = 0; \
    if (has_mode(flags)) { \
        va_list args; va_start(args, flags); \
        mode = va_arg(args, mode_t); va_end(args); \
    } \
    int (*real)(const char *, int, ...) = dlsym(RTLD_NEXT, #name); \
    if (!real) { errno = ENOSYS; return -1; } \
    return adapt(real(path, flags, mode), path, flags); \
}
OPEN_WRAPPER(open)
OPEN_WRAPPER(open64)

#define OPENAT_WRAPPER(name) \
int name(int dirfd, const char *path, int flags, ...) { \
    mode_t mode = 0; \
    if (has_mode(flags)) { \
        va_list args; va_start(args, flags); \
        mode = va_arg(args, mode_t); va_end(args); \
    } \
    int (*real)(int, const char *, int, ...) = dlsym(RTLD_NEXT, #name); \
    if (!real) { errno = ENOSYS; return -1; } \
    return adapt(real(dirfd, path, flags, mode), path, flags); \
}
OPENAT_WRAPPER(openat)
OPENAT_WRAPPER(openat64)

static FILE *adapt_stream(FILE *stream, const char *path, const char *mode) {
    int saved = errno;
    if (stream && mode[0] == 'r' && !strchr(mode, '+') && enabled(path, O_RDONLY)) {
        int fd = snapshot(fileno(stream), strchr(mode, 'e') ? O_CLOEXEC : 0);
        if (fd >= 0) {
            FILE *replacement = fdopen(fd, mode);
            if (replacement) { fclose(stream); stream = replacement; }
            else close(fd);
        }
    }
    errno = saved;
    return stream;
}

#define FOPEN_WRAPPER(name) \
FILE *name(const char *path, const char *mode) { \
    FILE *(*real)(const char *, const char *) = dlsym(RTLD_NEXT, #name); \
    if (!real) { errno = ENOSYS; return NULL; } \
    return adapt_stream(real(path, mode), path, mode); \
}
FOPEN_WRAPPER(fopen)
FOPEN_WRAPPER(fopen64)
