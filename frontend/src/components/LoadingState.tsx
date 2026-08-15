interface LoadingStateProps {
  message: string;
}

export function LoadingState({ message }: LoadingStateProps) {
  return <p className="loading-indicator">{message}</p>;
}