import * as React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';

interface ErrorBoundaryProps {
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  message: string;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, message: '' };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      message: error.message || 'Ocurrió un error inesperado al renderizar la vista.',
    };
  }

  handleReset = (): void => {
    this.setState({ hasError: false, message: '' });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-[320px] items-center justify-center p-6" role="alert">
          <Card className="max-w-md border-destructive/40">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-destructive">
                <AlertTriangle className="h-5 w-5" aria-hidden="true" />
                Algo salió mal
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">{this.state.message}</p>
            </CardContent>
            <CardFooter className="gap-2">
              <Button onClick={this.handleReset} variant="default">
                <RefreshCw className="h-4 w-4" aria-hidden="true" />
                Reintentar
              </Button>
              <Button onClick={() => window.location.reload()} variant="outline">
                Recargar página
              </Button>
            </CardFooter>
          </Card>
        </div>
      );
    }
    return this.props.children;
  }
}
