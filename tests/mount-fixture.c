#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Test-only second preload: supply mount fixtures without adding a production
 * environment variable that can replace the mount-table source. */
static const char *redirect(const char *path) {
    if (strcmp(path, "/proc/mounts") && strcmp(path, "/proc/self/mounts")) return path;
    if (getenv("TEST_MOUNTS_DENIED")) { errno = EACCES; return NULL; }
    const char *fixture = getenv("TEST_MOUNTS_FILE");
    return fixture ? fixture : path;
}

#define OPEN(name) \
int name(const char *path, int flags, ...) { \
    mode_t mode = 0; \
    if ((flags & O_CREAT) || (flags & O_TMPFILE) == O_TMPFILE) { \
        va_list args; va_start(args, flags); mode = va_arg(args, mode_t); va_end(args); \
    } \
    int (*real)(const char *, int, ...) = dlsym(RTLD_NEXT, #name); \
    path = redirect(path); \
    return path ? real(path, flags, mode) : -1; \
}
OPEN(open)
OPEN(open64)

#define OPENAT(name) \
int name(int dirfd, const char *path, int flags, ...) { \
    mode_t mode = 0; \
    if ((flags & O_CREAT) || (flags & O_TMPFILE) == O_TMPFILE) { \
        va_list args; va_start(args, flags); mode = va_arg(args, mode_t); va_end(args); \
    } \
    int (*real)(int, const char *, int, ...) = dlsym(RTLD_NEXT, #name); \
    path = redirect(path); \
    return path ? real(dirfd, path, flags, mode) : -1; \
}
OPENAT(openat)
OPENAT(openat64)

#define FOPEN(name) \
FILE *name(const char *path, const char *mode) { \
    FILE *(*real)(const char *, const char *) = dlsym(RTLD_NEXT, #name); \
    path = redirect(path); \
    return path ? real(path, mode) : NULL; \
}
FOPEN(fopen)
FOPEN(fopen64)

int memfd_create(const char *name, unsigned int flags) {
    if (getenv("TEST_MEMFD_DENIED")) { errno = EPERM; return -1; }
    int (*real)(const char *, unsigned int) = dlsym(RTLD_NEXT, "memfd_create");
    return real(name, flags);
}
