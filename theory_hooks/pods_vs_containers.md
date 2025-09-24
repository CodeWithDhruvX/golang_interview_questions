### Pods vs Containers

- **Container:** A single lightweight environment for running an app (e.g., `nginx`).
- **Pod:** A wrapper that contains one or more containers with shared storage and IP.

**Key Difference:**
- Container = Application instance.
- Pod = Group of containers + metadata.

**Analogy:** Pod = house, Container = people living inside.

**Pitfall:** Saying "Pod and Container are the same." Always highlight that a Pod can host multiple containers.