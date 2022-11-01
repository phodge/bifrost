export function assert_eq(val1: unknown, val2: unknown): void {
  if (val1 !== val2) {
    throw new Error(`${val1} !== ${val2}`);
  }
}

export function assert_islist(val: unknown, size: number): void {
  if (!Array.isArray(val)) {
    throw new Error("Value is not an Array");
  }

  if (val.length !== size) {
    throw new Error(`Array has size ${val.length} instead of ${size}`);
  }
}
