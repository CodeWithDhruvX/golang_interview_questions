### Why do we use Kubernetes?

We use Kubernetes to solve the **scaling and reliability problems** of running many containers.

- **Without Kubernetes:** You would need to manually start, stop, and connect containers.
- **With Kubernetes:**
  - Automates scaling (add/remove containers as needed)
  - Handles failures with self-healing
  - Provides service discovery & networking
  - Supports rolling updates without downtime

**Pitfall:** Don't just say "because it's popular." Instead, focus on how it **simplifies container management at scale.**