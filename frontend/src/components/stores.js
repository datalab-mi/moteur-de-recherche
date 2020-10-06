import { readable, writable } from 'svelte/store';

// auth: https://www.toptal.com/front-end/svelte-framework-guide
export const searchResults = writable({
  'hits':[],
  'threshold': 1
});

export const suggestEntry = writable([]);

export const isReindex = writable(false)

export const list_synonym = writable([])

//INDEX_NAME is replaced in rollup.config.js
export const index_name = writable('INDEX_NAME')
export const dstDir = "DST_DIR"
export const pjDir = "PJ_DIR"
