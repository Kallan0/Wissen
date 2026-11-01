declare module "@jsonresume/schema" {
  export function validate(
    resume: unknown,
    callback: (errors: unknown, valid: boolean) => void,
  ): void;
}
