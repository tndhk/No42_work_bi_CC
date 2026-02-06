import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useLogin } from '@/hooks';
import { useAuthStore } from '@/stores/auth-store';
import { useEffect } from 'react';

const loginSchema = z.object({
  email: z.string().email('有効なメールアドレスを入力してください'),
  password: z.string().min(1, 'パスワードを入力してください'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const loginMutation = useLogin();

  const { register, handleSubmit, formState: { errors } } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: 'admin@example.com',
      password: 'Admin@1234',
    },
  });

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/dashboards';

  useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, from]);

  const onSubmit = (data: LoginFormData) => {
    loginMutation.mutate(data, {
      onSuccess: () => {
        navigate(from, { replace: true });
      },
    });
  };

  return (
    <div className="flex min-h-screen">
      {/* Left panel - brand identity */}
      <div className="hidden lg:flex w-2/5 flex-col justify-between p-12 bg-[hsl(210,14%,11%)] relative overflow-hidden">
        {/* Decorative geometric lines */}
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
          {/* Diagonal teal accent lines */}
          <div className="absolute top-0 right-0 w-px h-[60%] bg-primary/20 origin-top-right rotate-[25deg] translate-x-[-80px] translate-y-[40px]" />
          <div className="absolute top-0 right-0 w-px h-[45%] bg-primary/10 origin-top-right rotate-[25deg] translate-x-[-120px] translate-y-[80px]" />
          <div className="absolute bottom-0 left-0 w-px h-[50%] bg-primary/15 origin-bottom-left rotate-[25deg] translate-x-[60px] translate-y-[-60px]" />
          {/* Grid dots */}
          <div className="absolute bottom-20 right-12 grid grid-cols-4 gap-3">
            {Array.from({ length: 16 }).map((_, i) => (
              <div
                key={i}
                className="w-1 h-1 rounded-full bg-primary/20"
              />
            ))}
          </div>
          {/* Horizontal teal rule */}
          <div className="absolute top-1/2 left-12 w-16 h-px bg-primary/30" />
        </div>

        {/* Brand content */}
        <div className="relative z-10">
          <h1 className="text-primary font-mono text-4xl font-semibold uppercase tracking-[0.25em] leading-tight">
            BI Tool
          </h1>
          <p className="mt-3 text-[hsl(210,8%,60%)] font-mono text-sm tracking-wider uppercase">
            Business Intelligence Platform
          </p>
          <div className="mt-6 h-px w-12 bg-primary/40" />
        </div>

        {/* Bottom tagline */}
        <div className="relative z-10">
          <p className="text-[hsl(210,8%,40%)] text-xs font-mono tracking-wider">
            Arctic Precision
          </p>
        </div>
      </div>

      {/* Right panel - login form */}
      <div className="flex-1 flex items-center justify-center p-6 lg:p-12 bg-background">
        <div className="w-full max-w-sm animate-fade-in-up">
          {/* Mobile brand (visible only below lg) */}
          <div className="mb-10 lg:hidden">
            <h1 className="text-primary font-mono text-2xl font-semibold uppercase tracking-[0.2em]">
              BI Tool
            </h1>
          </div>

          {/* Heading */}
          <div className="mb-8">
            <h2 className="text-2xl font-semibold tracking-tight text-foreground">
              Sign In
            </h2>
            <div className="mt-2 h-0.5 w-8 rounded-full bg-primary" />
            <p className="mt-3 text-sm text-muted-foreground">
              アカウントにログインしてください
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                メールアドレス
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="user@example.com"
                className="h-11 bg-background border-input px-4 text-sm placeholder:text-muted-foreground/50 focus-visible:ring-primary/30"
                {...register('email')}
              />
              {errors.email && (
                <p className="text-xs text-destructive pt-1">{errors.email.message}</p>
              )}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password" className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                パスワード
              </Label>
              <Input
                id="password"
                type="password"
                className="h-11 bg-background border-input px-4 text-sm focus-visible:ring-primary/30"
                {...register('password')}
              />
              {errors.password && (
                <p className="text-xs text-destructive pt-1">{errors.password.message}</p>
              )}
            </div>
            {loginMutation.isError && (
              <p className="text-xs text-destructive">
                メールアドレスまたはパスワードが正しくありません
              </p>
            )}
            <div className="pt-2">
              <Button
                type="submit"
                className="w-full h-11 text-sm font-medium tracking-wide"
                disabled={loginMutation.isPending}
              >
                {loginMutation.isPending ? 'ログイン中...' : 'ログイン'}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
