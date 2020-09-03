import { readable, writable } from 'svelte/store';

// auth: https://www.toptal.com/front-end/svelte-framework-guide
export const searchInput = writable({
  content: {
    value: "",
    type: "text",
    placeholder: "Recherche par mots clefs",
    innerHtml: ""
    },
  author: {
    value: "",
    type: "text",
    placeholder: "Paul Dupond, Anne-Marie",
    innerHtml: "Nom ou Prénom"

  },
  from_date: {
    value: "",
    type: "text",
    placeholder: "01/01/2018",
    innerHtml: "A partir de : "

  },
  to_date: {
    value: "",
    type: "text",
    placeholder: "01/01/2018",
    innerHtml: "Jusqu'à : "
  }
  }
)

export const searchResults = writable({
  'hits':[],
  'threshold':1
});

export const suggestEntry = writable([]);

export const index_name = writable('iga')
export const isReindex = writable(false)

export const list_synonym = writable([])

// The const item describe the behaviour and the display of an item.
// The key should match with their elasticsearch counterparts
export const item = readable({
  multiple: true,
  accept: '.pdf',
  new: [
        {
          key: 'title',
          type: 'text',
          placeholder: 'Renseigner le titre',
          value: '',
          innerHtml: ''
        },
        {
          key: 'author',
          type: 'text',
          placeholder: 'Séparez les par des virgules',
          value: '',
          innerHtml: '<b>Auteurs :</b>'
        },
        {
          key: 'date',
          type: 'date',
          placeholder: 'Date',
          value: '',
          innerHtml: '<b>Date :</b>'
        }
          ],
    result: [
        {
          key: 'title',
          type: 'text',
          placeholder: 'NA',
          value: '',
          innerHtml: ''
        },
        {
          key: 'author',
          type: 'text',
          placeholder: 'NA',
          value: '',
          innerHtml: '<b>Auteurs :</b>'
        },
        {
          key: 'date',
          type: 'date',
          value: '',
          innerHtml: '<b>Date :</b>'
        }
          ]
})
