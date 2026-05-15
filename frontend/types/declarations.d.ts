// Type declarations for packages that don't resolve with bundler moduleResolution + Babel

declare module "class-variance-authority" {
  export type VariantProps<T extends (...args: any) => any> = Partial<
    Exclude<Parameters<T>[0], undefined>
  >;
  export function cva(
    base: string,
    config?: {
      variants?: Record<string, Record<string, string>>;
      defaultVariants?: Record<string, string>;
    }
  ): (props?: Record<string, string | null | undefined>) => string;
}
