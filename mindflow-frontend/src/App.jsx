import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './hooks/useAuth';
import EnhancedDashboard from './components/EnhancedDashboard.jsx';
import './App.css';
// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <EnhancedDashboard />
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
