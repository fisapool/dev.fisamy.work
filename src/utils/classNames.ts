/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * Utility function to conditionally combine CSS class names
 * @param classes - Array of class names, can include false/null/undefined values
 * @returns Combined class names as a string
 */
export function classNames(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(" ");
}

