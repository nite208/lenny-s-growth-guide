import { Component } from "react";

export default class AppErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error) {
    console.error("frontend_error_boundary", error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gray-950 text-gray-100 flex items-center justify-center px-4">
          <div className="max-w-md text-center">
            <h1 className="text-lg font-semibold mb-2">Backend unreachable</h1>
            <p className="text-sm text-gray-400">
              We couldn&apos;t connect to The Lenny Growth Assistant backend. Check that the API is
              running and refresh.
            </p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
