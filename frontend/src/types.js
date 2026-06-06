/**
 * @typedef {Object} ChapterItem
 * @property {number} chapter_number
 * @property {string} title
 * @property {string} heading
 * @property {string} content
 * @property {number} char_count
 * @property {number} paragraph_count
 */

/**
 * @typedef {Object} ChapterParseResult
 * @property {boolean} valid
 * @property {number} chapter_count
 * @property {number} min_chapters_required
 * @property {string} message
 * @property {string} preamble
 * @property {ChapterItem[]} chapters
 */

export {};
