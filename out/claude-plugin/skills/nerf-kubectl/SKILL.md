---
name: nerf-kubectl
description: "kubectl tools for inspecting and operating on Kubernetes clusters"
targets: ["*"]
---

# nerf-kubectl

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

Tools for inspecting and operating on Kubernetes clusters. All tools
are template-mode wrappers, so the agent can only pass the parameters
declared here -- no arbitrary kubectl flags, no connection overrides,
no short-flag stacks. Output is always JSON where applicable; pipe
through jq for advanced extraction. kubectl-get refuses Secrets;
use kubectl-get-secrets, which scrubs .data / .stringData / the
last-applied-configuration annotation. Use az-aks-get-credentials
to populate ~/.kube/config first, then kubectl-config-use-context
to switch between configured clusters.

## nerf-kubectl-version

Show kubectl client and server version.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-kubectl/scripts/nerf-kubectl-version`
**Maps to:** `kubectl version --output json`

No arguments.

---

## nerf-kubectl-config-get-contexts

List configured kubectl contexts.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-kubectl/scripts/nerf-kubectl-config-get-contexts`
**Maps to:** `kubectl config get-contexts`

No arguments.

---

## nerf-kubectl-config-current-context

Show the currently active kubectl context.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-kubectl/scripts/nerf-kubectl-config-current-context`
**Maps to:** `kubectl config current-context`

No arguments.

---

## nerf-kubectl-config-use-context

Switch to a different kubectl context. Marked admin because activating an admin-account context (e.g. one fetched via az-aks-get-credentials-admin) gives every subsequent kubectl call cluster-admin powers; the threat marker on this tool has to be at least as strict as the credential fetch that wrote the context. The harness should default-deny this tool whenever it default- denies az-aks-get-credentials-admin.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-kubectl/scripts/nerf-kubectl-config-use-context <context>`
**Maps to:** `kubectl config use-context <context>`

**Arguments:**

- `<context>` (required): Context name (from kubectl-config-get-contexts). must match `^[a-zA-Z0-9_]([a-zA-Z0-9._-]*[a-zA-Z0-9_])?$`

---

## nerf-kubectl-cluster-info

Show cluster info (API server URL, addons).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-kubectl/scripts/nerf-kubectl-cluster-info`
**Maps to:** `kubectl cluster-info`

No arguments.

---

## nerf-kubectl-get

Get kubernetes resources. Returns JSON; pipe through jq for extraction. Refuses Secrets -- use kubectl-get-secrets instead, which redacts .data and .stringData.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-kubectl/scripts/nerf-kubectl-get [--all-namespaces|-A] [--show-labels] [--namespace|-n <namespace>] [--selector|-l <selector>] [--field-selector <field_selector>] <resource> [<name>]`
**Maps to:** `kubectl get <resource> <name> <namespace> <all_namespaces> <selector> <field_selector> <show_labels> --output json`

**Switches:**

- `--all-namespaces, -A`: List across all namespaces
- `--show-labels`: Include labels in the output

**Options:**

- `--namespace|-n` (optional): Namespace. must match `^[a-z0-9-]+$`
- `--selector|-l` (optional): Label selector (e.g. app=foo,env!=prod)
- `--field-selector` (optional): Field selector (e.g. status.phase=Running)

**Arguments:**

- `<resource>` (required): Resource type (e.g. pods, services, deployments) or "kind/name". must match `^[a-z][a-zA-Z0-9.-]*(/[a-zA-Z0-9._-]+)?$`
- `<name>` (optional): Specific resource name (optional). must match `^[a-zA-Z0-9._-]+$`

---

## nerf-kubectl-get-secrets

List Secret metadata with .data, .stringData, and ALL metadata.annotations removed. Cannot reveal secret values. Annotations are dropped wholesale because kubectl apply stores the rendered manifest (including .data) in the last-applied-configuration annotation, and operator-injected annotations may carry sensitive content. Labels are preserved. For secret values, go through az-keyvault or the secret-syncing source.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-kubectl/scripts/nerf-kubectl-get-secrets [--all-namespaces|-A] [--namespace|-n <namespace>] [--selector|-l <selector>] [<name>]`

**Switches:**

- `--all-namespaces, -A`: List across all namespaces

**Options:**

- `--namespace|-n` (optional): Namespace. must match `^[a-z0-9-]+$`
- `--selector|-l` (optional): Label selector

**Arguments:**

- `<name>` (optional): Specific secret name (optional). must match `^[a-z0-9.-]+$`

---

## nerf-kubectl-describe

Describe a kubernetes resource. Refuses Secrets because "kubectl describe" prints the metadata.annotations section verbatim, and any Secret created via "kubectl apply" carries a kubectl.kubernetes.io/last-applied-configuration annotation containing the original (base64-encoded) .data, which would bypass kubectl-get-secrets' redaction.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-kubectl/scripts/nerf-kubectl-describe [--namespace|-n <namespace>] <resource> <name>`
**Maps to:** `kubectl describe <resource> <name> <namespace>`

**Options:**

- `--namespace|-n` (optional): Namespace. must match `^[a-z0-9-]+$`

**Arguments:**

- `<resource>` (required): Resource type (e.g. pod, deployment). must match `^[a-z][a-zA-Z0-9.-]*$`
- `<name>` (required): Resource name. must match `^[a-zA-Z0-9._-]+$`

---

## nerf-kubectl-logs

Fetch pod logs (no follow). Use --tail to cap the line count. Combine with kubectl-get to poll if you need updates.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-kubectl/scripts/nerf-kubectl-logs [--previous|-p] [--namespace|-n <namespace>] [--container|-c <container>] [--tail <tail>] <pod>`
**Maps to:** `kubectl logs <pod> <namespace> <container> <tail> <previous>`

**Switches:**

- `--previous, -p`: Get logs from a previous container instance (after a crash/restart)

**Options:**

- `--namespace|-n` (optional): Namespace. must match `^[a-z0-9-]+$`
- `--container|-c` (optional): Container name (when the pod has multiple). must match `^[a-z0-9]([-a-z0-9]*[a-z0-9])?$`
- `--tail` (optional): Number of recent lines to fetch. must match `^[0-9]+$`

**Arguments:**

- `<pod>` (required): Pod name (or "pod/<name>" form). must match `^(pod/)?[a-z0-9]([-a-z0-9.]*[a-z0-9])?$`

---

## nerf-kubectl-top-pods

Show CPU and memory usage of pods.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-kubectl/scripts/nerf-kubectl-top-pods [--all-namespaces|-A] [--namespace|-n <namespace>] [--selector|-l <selector>]`
**Maps to:** `kubectl top pods <namespace> <all_namespaces> <selector>`

**Switches:**

- `--all-namespaces, -A`: List across all namespaces

**Options:**

- `--namespace|-n` (optional): Namespace. must match `^[a-z0-9-]+$`
- `--selector|-l` (optional): Label selector

---

## nerf-kubectl-top-nodes

Show CPU and memory usage of nodes.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-kubectl/scripts/nerf-kubectl-top-nodes [--selector|-l <selector>]`
**Maps to:** `kubectl top nodes <selector>`

**Options:**

- `--selector|-l` (optional): Label selector

---

## nerf-kubectl-api-resources

List API resources supported by the cluster (resource names only).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-kubectl/scripts/nerf-kubectl-api-resources [--api-group <api_group>]`
**Maps to:** `kubectl api-resources --output name <api_group>`

**Options:**

- `--api-group` (optional): Filter by API group (e.g. apps, batch). must match `^[a-z0-9.-]*$`

---

## nerf-kubectl-api-versions

List API group/versions supported by the cluster.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-kubectl/scripts/nerf-kubectl-api-versions`
**Maps to:** `kubectl api-versions`

No arguments.

---

## nerf-kubectl-explain

Show the schema documentation for a resource or field path.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-kubectl/scripts/nerf-kubectl-explain [--recursive] <resource>`
**Maps to:** `kubectl explain <resource> <recursive>`

**Switches:**

- `--recursive`: Print the entire schema recursively

**Arguments:**

- `<resource>` (required): Resource type or field path (e.g. pod, pod.spec.containers). must match `^[a-z][a-zA-Z0-9.-]*$`

---

## nerf-kubectl-exec

Execute a command in a pod (non-interactive, no TTY). Use this for one-shot diagnostics; for cluster mutations prefer Helm/Terraform.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-kubectl/scripts/nerf-kubectl-exec [--namespace|-n <namespace>] [--container|-c <container>] <pod> <command...>`
**Maps to:** `kubectl exec <pod> <namespace> <container> -- <command>`

**Options:**

- `--namespace|-n` (optional): Namespace. must match `^[a-z0-9-]+$`
- `--container|-c` (optional): Container name (when the pod has multiple containers). must match `^[a-z0-9]([-a-z0-9]*[a-z0-9])?$`

**Arguments:**

- `<pod>` (required): Pod name. must match `^[a-z0-9]([-a-z0-9.]*[a-z0-9])?$`
- `<command...>` (required): Command and args to run in the pod

---

## nerf-kubectl-port-forward

Forward a local port to a pod or service in the cluster. Wrapped with coreutils "timeout" so unattended runs cannot hang -- the forward is terminated after --timeout-seconds (required). Note that the wrapper exits 124 (the standard "timeout" exit code) when the time bound is reached; this is the expected success path for unattended diagnostics.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-kubectl/scripts/nerf-kubectl-port-forward --timeout-seconds <timeout_seconds> [--namespace|-n <namespace>] <target> <ports>`
**Maps to:** `timeout <timeout_seconds> kubectl port-forward <namespace> <target> <ports>`

**Options:**

- `--timeout-seconds` (required): Maximum seconds to keep the forward open (required; passed to coreutils timeout). must match `^[1-9][0-9]*$`
- `--namespace|-n` (optional): Namespace. must match `^[a-z0-9-]+$`

**Arguments:**

- `<target>` (required): Resource to forward to (e.g. pod/<name> or svc/<name>). must match `^(pod|svc|service|deployment|deploy|statefulset|sts)/[a-z0-9]([-a-z0-9.]*[a-z0-9])?$`
- `<ports>` (required): Port mapping (local:remote). must match `^[0-9]+:[0-9]+$`

---

## nerf-kubectl-rollout-restart

Trigger a rolling restart of a deployment, daemonset, or statefulset.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-kubectl/scripts/nerf-kubectl-rollout-restart [--namespace|-n <namespace>] <target>`
**Maps to:** `kubectl rollout restart <namespace> <target>`

**Options:**

- `--namespace|-n` (optional): Namespace. must match `^[a-z0-9-]+$`

**Arguments:**

- `<target>` (required): Resource to restart (e.g. deployment/<name>). must match `^(deployment|deploy|daemonset|ds|statefulset|sts)/[a-z0-9]([-a-z0-9.]*[a-z0-9])?$`

---
