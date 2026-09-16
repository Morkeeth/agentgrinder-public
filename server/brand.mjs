/* The one place the public product name and tagline are written.
 * Every user-visible string in site/, server/ and api/ derives from these two
 * constants, either by import or by the __BRAND__ and __TAGLINE__ build tokens
 * that scripts/build-site.mjs replaces. Renaming the product is one edit here.
 * Internal identifiers, the package name, the CLI command and the database
 * schema are deliberately not derived from this file.
 * Ruling 2026-09-16 09:22: the public product is STRIVE, tagline Post your strides.
 */
export const BRAND='STRIVE';
export const TAGLINE='Post your strides';
export const SERVICE=BRAND.toLowerCase();
