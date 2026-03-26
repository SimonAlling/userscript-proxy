import type { Result } from "./results";

/**
 * A `Promise` that doesn't reject, instead using {@link Result} to represent success/failure.
 */
export type NoRejectPromise<T, E> = Promise<Result<T, E>>;
