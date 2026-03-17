export function throwIfNullOrUndefined<T>(
  x: T,
  descriptionOfIt: DescriptionOrRedundanceHint<T>,
): NonNullable<T> {
  if (x == null) {
    throw new TypeError(
      `throwIfNullOrUndefined: ${descriptionOfIt} was unexpectedly ${JSON.stringify(x)}.`,
    );
  }

  return x;
}

type DescriptionOrRedundanceHint<T> = null extends T
  ? string
  : undefined extends T
    ? string
    : `It cannot be null or undefined; this check is redundant.`;
