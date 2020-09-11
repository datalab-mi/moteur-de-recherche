import { readable, writable } from 'svelte/store';

// auth: https://www.toptal.com/front-end/svelte-framework-guide
export const searchList = writable([
  [
    {
    bool: "must",
    clause: "multi_match",
    fields: ["titre", "question" , "reponse"],
    query: "",
    type: "search",
    placeholder: "Recherche par mots clefs",
    innerHtml: "",
    style: "w-3/4 p-2",
    highlight: true
    }
  ]
]
)

export const searchResults = writable({
  'hits':[],
  'threshold':1
});

export const suggestEntry = writable([]);

export const index_name = writable('bld')
export const isReindex = writable(false)

export const list_synonym = writable([])

// The const item describe the behaviour and the display of an item.
// The key should match with their elasticsearch counterparts
export const item = readable({
  multiple: false,
  accept: '.odt',
  inputs: [
    {
      key: 'titre',
      type: 'text',
      placeholder: 'NA',
      value: '',
      innerHtml: '',
      metadata: false
    },
    {
      key: 'question',
      type: 'textarea',
      placeholder: 'NA',
      value: '',
      innerHtml: '<b>Question :</b>',
      highlight: true,
      metadata: false

    },
    {
      key: 'reponse',
      type: 'textarea',
      placeholder: 'NA',
      value: '',
      innerHtml: '<b>Réponse :</b>',
      highlight: false,
      metadata: true
    },
    {
      key: 'pieces jointes',
      type: 'text',
      placeholder: 'NA',
      value: '',
      innerHtml: '<b>Pièces jointes :</b>',
      metadata: false
    }
  ]

})
