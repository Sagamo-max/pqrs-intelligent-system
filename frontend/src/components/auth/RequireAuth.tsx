import * as React from 'react';
import { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { fetchMe } from '@/api/auth';
import { PageLoader } from '@/components/common/PageLoader';
import { useAuthStore } from '@/stores/authStore';

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const { accessToken, user, setUser, logout } = useAuthStore();

  useEffect(() => {
    let active = true;
    if (accessToken && !user) {
      fetchMe()
        .then((profile) => {
          if (active) {
            setUser(profile);
          }
        })
        .catch(() => {
          if (active) {
            logout();
          }
        });
    }
    return () => {
      active = false;
    };
  }, [accessToken, user, setUser, logout]);

  if (!accessToken) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (!user) {
    return <PageLoader />;
  }

  return <>{children}</>;
}
