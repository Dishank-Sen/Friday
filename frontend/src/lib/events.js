// The current backend has no task event endpoint or event stream to subscribe to.
export function subscribeToTaskEvents() {
  return {
    supported: false,
    close() {},
  };
}
