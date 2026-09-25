#define _GNU_SOURCE
#include <dlfcn.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/un.h>

/* Snap's network-bind policy permits abstract sockets in its own namespace.
 * Calibre uses abstract sockets for single-instance locks and GUI/viewer IPC.
 * Translate only Calibre sockets, in both Python and Qt, without changing the
 * upstream bundle or touching filesystem, display, or other service sockets. */
static const struct sockaddr *translate(const struct sockaddr *address,
                                       socklen_t *length,
                                       struct sockaddr_un *mapped) {
    const size_t offset = offsetof(struct sockaddr_un, sun_path);
    if (!address || address->sa_family != AF_UNIX ||
        *length <= offset + 1 || *length > sizeof(*mapped))
        return address;
    const struct sockaddr_un *unix_address = (const void *)address;
    if (unix_address->sun_path[0] != '\0')
        return address;
    size_t size = *length - offset - 1;
    char name[sizeof(mapped->sun_path)] = {0};
    memcpy(name, unix_address->sun_path + 1, size);
    if (strncmp(name, "calibre-singleinstance-", 22) != 0 &&
        strstr(name, "-calibre-") == NULL)
        return address;
    const char prefix[] = "snap.calibre.";
    if (sizeof(prefix) - 1 + size > sizeof(mapped->sun_path) - 1)
        return address;
    memset(mapped, 0, sizeof(*mapped));
    mapped->sun_family = AF_UNIX;
    memcpy(mapped->sun_path + 1, prefix, sizeof(prefix) - 1);
    memcpy(mapped->sun_path + sizeof(prefix), unix_address->sun_path + 1, size);
    *length += sizeof(prefix) - 1;
    return (const void *)mapped;
}

int bind(int fd, const struct sockaddr *address, socklen_t length) {
    int (*real_bind)(int, const struct sockaddr *, socklen_t) = dlsym(RTLD_NEXT, "bind");
    struct sockaddr_un mapped;
    address = translate(address, &length, &mapped);
    return real_bind(fd, address, length);
}

int connect(int fd, const struct sockaddr *address, socklen_t length) {
    int (*real_connect)(int, const struct sockaddr *, socklen_t) = dlsym(RTLD_NEXT, "connect");
    struct sockaddr_un mapped;
    address = translate(address, &length, &mapped);
    return real_connect(fd, address, length);
}
