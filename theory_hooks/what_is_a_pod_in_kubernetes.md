### What is a Pod in Kubernetes?

A **Pod** is the **smallest deployable unit** in Kubernetes.

- **Contains:** One or more tightly coupled containers.
- **Purpose:** Runs together, shares storage, network, and namespace.
- **Analogy:** A Pod is like a **box** holding one or more toys (containers) that always move together.

**Example:**
- A web app container + sidecar logging container in the same Pod.

**Pitfall:** Don't confuse Pods with Containers. Containers run inside Pods, not the other way around.