import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { createClient, Session } from '@supabase/supabase-js';

// Types
interface AuthUser {
  id: string;
  email: string | null;
  user_metadata?: any;
}

interface AuthContextType {
  user: AuthUser | null;
  session: Session | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<{ error: string | null }>;
  signUp: (email: string, password: string) => Promise<{ error: string | null }>;
  signOut: () => Promise<void>;
  signInWithGoogle: () => Promise<{ error: string | null }>;
  getAccessToken: () => string | null;
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Provider component
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  // Create Supabase client
  const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || '';
  const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || '';
  
  const supabase = createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true
    }
  });

  // Initialize auth state
  useEffect(() => {
    // Check for OAuth callback
    const hash = window.location.hash;
    const query = window.location.search;
    
    if (hash.includes('access_token') || query.includes('code=')) {
      console.log('OAuth callback detected, processing...');
      // Supabase client with detectSessionInUrl will automatically handle this
      // Wait a moment for Supabase to process the session
      setTimeout(() => {
        // Clear the URL hash/query to clean up the URL
        window.history.replaceState({}, document.title, window.location.pathname);
      }, 500);
    }
    
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ? {
        id: session.user.id,
        email: session.user.email ?? null,
        user_metadata: session.user.user_metadata
      } : null);
      setLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event: any, session: Session | null) => {
      setSession(session);
      setUser(session?.user ? {
        id: session.user.id,
        email: session.user.email ?? null,
        user_metadata: session.user.user_metadata
      } : null);
    });

    return () => subscription.unsubscribe();
  }, []);

  // Email/Password sign in
  const signIn = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    return { error: error?.message || null };
  };

  // Email/Password sign up
  const signUp = async (email: string, password: string) => {
    const { error } = await supabase.auth.signUp({
      email,
      password,
    });

    return { error: error?.message || null };
  };

  // Google OAuth sign in
  const signInWithGoogle = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: window.location.origin
      }
    });
    
    return { error: error?.message || null };
  };

  // Sign out
  const signOut = async () => {
    await supabase.auth.signOut();
  };

  // Get access token for API calls
  const getAccessToken = () => {
    return session?.access_token || null;
  };

  const value: AuthContextType = {
    user,
    session,
    loading,
    signIn,
    signUp,
    signOut,
    signInWithGoogle,
    getAccessToken,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Hook for using auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
