<script>
	import BaseItem from './BaseItem.svelte'
	import PutItem from './PutItem.svelte'

	import { index_name, item } from './stores.js';
	import { index, upload } from './utils.js'

	export let _id;
	export let _source;
	export let _score;

	export let highlight = {'content':''};

	$: filename = _id.replace(/\+/g, " ")
	//$: url = `/web/viewer.html?file=%2Fuser%2Fpdf%2F${filename}`
	$: url = `/api/common/files/pdf/${filename}`

	let promiseDelete = new Promise(()=>{});
	let promiseDeleteIndex = new Promise(()=>{});

	let readonly = true;
	let send = false;
	let meta = [];

	let isResult = true;

	// replace value to the result value contained in _source
	$: {
		meta = []
		$item.result.forEach((item, index) => {
			item.value = _source[item.key]
			meta.push(item)
		})

		console.log(meta)
	}

	const file = {'name': _id.replace(/\+/g, " ")}

	async function remove() {
		const res = await fetch(`/api/admin/${filename}`,
				{method: 'DELETE'});
		if (res.ok || res.status == 404) {
			return res.status
		} else {
			console.log('error')
			throw new Error('Oups');
		}
	}

	function handleDelete() {
		console.log(`Delete ${_id.replace(/\+/g, " ")}`)
		promiseDelete = remove()
		promiseDeleteIndex = index( $index_name, filename, 'DELETE')
	}

	function handleSave() {
		send = !send
		readonly = !readonly
	}
</script>

<BaseItem meta={meta} bind:readonly={readonly} cssClass='result'>

	<div slot="highlight">
		{#if highlight.content != ''}
			<p> &laquo; {@html highlight.content.join(' [...] ')} &raquo; </p>
		{/if}
	</div>

	<div slot="score">
		{#if _score != 0}
				<p>Score : {Math.round((_score + Number.EPSILON) * 100) / 100}</p>
		{/if}
	</div>

	<div slot="button">
		<button on:click="{window.open(url,'_blank')}" class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded inline-flex items-center">
		<svg class="fill-current w-4 h-4 mr-2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M.2 10a11 11 0 0 1 19.6 0A11 11 0 0 1 .2 10zm9.8 4a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm0-2a2 2 0 1 1 0-4 2 2 0 0 1 0 4z"/></svg>
			<span>CONSULTER</span>
		</button>

		<button on:click={handleDelete} class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded inline-flex items-center">
			<svg class="fill-current w-4 h-4 mr-2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M6 2l2-2h4l2 2h4v2H2V2h4zM3 6h14l-1 14H4L3 6zm5 2v10h1V8H8zm3 0v10h1V8h-1z"/></svg>
			<span>SUPPRIMER</span>
		</button>

		{#if (readonly & send) }
			<button on:click={handleSave} class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded inline-flex items-center">
				<svg class="fill-current w-4 h-4 mr-2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M12.3 3.7l4 4L4 20H0v-4L12.3 3.7zm1.4-1.4L16 0l4 4-2.3 2.3-4-4z"/></svg>
				<span>MODIFER</span>
			</button>
			<PutItem meta={meta} file={file} />
		{:else if (!readonly & !send) }
			<button on:click={handleSave} class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded inline-flex items-center">
				<svg class="fill-current w-4 h-4 mr-2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M0 2C0 .9.9 0 2 0h14l4 4v14a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V2zm5 0v6h10V2H5zm6 1h3v4h-3V3z"/></svg>
					<span>SAUVER</span>

			</button>
		{:else}
			<button on:click="{() => readonly = !readonly}" class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded inline-flex items-center">
				<svg class="fill-current w-4 h-4 mr-2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M12.3 3.7l4 4L4 20H0v-4L12.3 3.7zm1.4-1.4L16 0l4 4-2.3 2.3-4-4z"/></svg>
				<span>MODIFER</span>
			</button>
		{/if}



		{#await promiseDelete}
		{:then status}
			{#if status == 204 }
				<p style="color: green"> Le fichier {filename} est supprimé</p>
			{:else if status == 404 }
				<p style="color: red" > {filename} n'existe pas</p>
			{:else}
				<p>Status {status} non connu</p>
			{/if}
		{:catch error}
			<p style="color: red">{error.message}</p>
		{/await}

		{#await promiseDeleteIndex}
		{:then status}
			{#if status == 200 }
				<p style="color: green"> {filename} désindexé</p>
			{:else if status == 404 }
				<p style="color: red" > {filename} pas dans l'index</p>
			{:else}
				<p>Status {status} non connu</p>
			{/if}
		{:catch error}
			<p style="color: red">{error.message}</p>
		{/await}

	</div>


</BaseItem>

<style>

</style>
