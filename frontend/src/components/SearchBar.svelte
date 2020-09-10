<script>
	import { searchInput, searchResults, suggestEntry,  index_name } from '../components/stores.js';
	import SearchInputComponent from  '../components/SearchInputComponent.svelte';
	let promiseSearch =  new Promise(()=>{});
	let promiseSuggest =  new Promise(()=>{});

	let body; // searchInput in dict format
	//let searchInputList = $searchInputObject.entries($searchInput)
	//console.log(searchInputList)

	const format2ES = (query_list) => {
		let query_dic = {index_name: $index_name, must: [], should: [], filter: [], highlight: []};
		let obj;
		let highlight_fields = []
		console.log(query_list)
		for (obj of query_list) {
			let clause = {}
			if (obj.query != "") {
				highlight_fields.push(obj.fields)
				if (obj.bool === "must") {
					clause[obj.clause] = {fields: obj.fields, query: obj.query}
				} else if  (obj.bool === "filter") {
					clause[obj.clause] = {[obj.fields]: obj.query}
				}
				query_dic[obj.bool].push(clause)
			}

		}
		query_dic["highlight"] = highlight_fields.flat()
		return query_dic
  };

	async function search() {

		body = format2ES($searchInput.flat(2))
		// convert $searchInput to post json
		//body = $searchInput.flat(2).reduce(function(map, obj) {
		//		map[obj.bool] = {fields: obj.fields, query: obj.query};
		//		return map;
		//}, {index_name: $index_name});
		//console.log($searchInput)

		const res = await fetch("/api/common/search",{
												method: "POST",
												body: JSON.stringify(body)
													 });

		const items = await res.json();
		if (res.ok) {
			$searchResults = items
			return items.hits.length;
		} else {
			throw new Error('Oups');
		}
	}


	async function suggest() {
		console.log($searchInput.content.value)
		const res = await fetch("/api/common/suggest",{
												method: "POST",
												body: JSON.stringify({
															 index_name: $index_name,
															 content: $searchInput.content.value,
														 })
													 });

		const items = await res.json();
		//console.log(items)
		if (res.ok) {
			$suggestEntry = items
			return "ok";
		} else {
			throw new Error('Oups');
		}
	}

	function handleSearch() {
		promiseSearch = search();
	}

	function handleSuggest() {
		console.log('handleSuggest')
		promiseSuggest = suggest();
	}

	function handleSuggestChosen(v) {
		//$searchInput.content.value = e.target.innerHTML
		$searchInput.content.value = v
		$suggestEntry = []
	}

promiseSearch = search();

</script>
<div class='search-bar'>
	{#each $searchInput as row, i }
	<div class="flex mb-4">

		{#each row as {bool, clause, fields, query, type, placeholder, innerHtml, style}, j}
			{#if (i === 0) && (j === 0) }
				<div class="w-1/4 p-2" >
					<button on:click={handleSearch} class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded inline-flex items-center">
						<svg class="fill-current w-4 h-4 mr-2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M12.9 14.32a8 8 0 1 1 1.41-1.41l5.35 5.33-1.42 1.42-5.33-5.34zM8 14A6 6 0 1 0 8 2a6 6 0 0 0 0 12z"/></svg>
						<span>Rechercher</span>
					</button>
				</div>
			{/if}

			<SearchInputComponent {bool} {clause} {fields} bind:query {type} {placeholder} {innerHtml} {style} />
		{/each}
		</div>

	{/each}

{#await promiseSearch}
	<p>...Attente de la requête</p>

{:then length}
	<p>{length} documents trouvés</p>

{:catch error}
	<p style="color: red">{error.message}</p>
{/await}

</div>
<!--
<div class='search-bar'>

	<div class="flex mb-4">
		<div class="w-3/4 p-2" >
			<div class="flex flex-col px-2">
				<div class="px-2" >
				<label> {@html $searchInput.content.innerHtml}
					<input type="search" bind:value={$searchInput.content.value}
					       placeholder={$searchInput.content.placeholder}
								 on:input={handleSuggest}
								 class="bg-white focus:outline-none focus:shadow-outline border border-gray-300 rounded-lg py-2 px-4 block w-full appearance-none leading-normal">

				<div class="px-2" id="suggest">
					{#each $suggestEntry as {text, highlighted} }
				     <div class="bg-white hover:bg-gray-500" on:click="{e => handleSuggestChosen(text)}">
						 	{@html highlighted}
						 </div>
					 {/each}
				</div>
				</label>
				</div>

			<div class="flex mb-4">
				{#if $searchInput.author}
					<div class="w-2/4 px-2">
						<label> {@html $searchInput.author.innerHtml}
							<input type="search" bind:value={$searchInput.author.value}
										 placeholder={$searchInput.author.placeholder}
										class="bg-white focus:outline-none focus:shadow-outline border border-gray-300 rounded-lg py-2 px-4 block w-full appearance-none leading-normal">
						</label>
					</div>
				{/if}

				<div class="w-1/4 px-2" >
				<label> {@html $searchInput.from_date.innerHtml}
					<input type="date" bind:value={$searchInput.from_date.value}
					       placeholder={$searchInput.from_date.placeholder}
								  class="bg-white focus:outline-none focus:shadow-outline border border-gray-300 rounded-lg py-2 px-4 block w-full appearance-none leading-normal">
				</label>
				</div>
				<div class="w-1/4 px-2" >
					<label> {@html $searchInput.to_date.innerHtml}
						<input type="date" bind:value={$searchInput.to_date.value}
									 placeholder={$searchInput.to_date.placeholder}
										class="bg-white focus:outline-none focus:shadow-outline border border-gray-300 rounded-lg py-2 px-4 block w-full appearance-none leading-normal">
					</label>
				</div>
			</div>

			</div>

		</div>
		<div class="w-1/4 px-2" >
			<button on:click={handleSearch} class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded inline-flex items-center">
				<svg class="fill-current w-4 h-4 mr-2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M12.9 14.32a8 8 0 1 1 1.41-1.41l5.35 5.33-1.42 1.42-5.33-5.34zM8 14A6 6 0 1 0 8 2a6 6 0 0 0 0 12z"/></svg>
				<span>Rechercher</span>
			</button>
		</div>

	</div>

	{#if $searchInput.content.value!=''}
		<h1>La recherche est : {$searchInput.content.value}</h1>
	{/if}

	{#await promiseSearch}
		<p>...Attente de la requête</p>

	{:then length}
		<p>{length} documents trouvés</p>

	{:catch error}
		<p style="color: red">{error.message}</p>
	{/await}

</div>
 //-->
<style>
	.search-bar {
		width: 100%;
		border: 1px solid #aaa;
		border-radius: 4px;
		box-shadow: 2px 2px 8px rgba(0,255,0,1);
		padding: 1em;
		margin: 0 0 1em 0;
	}

	#suggest {
			z-index: 2;
			position: absolute;
			background-color: rgba(255,255,255,1);
		}
	</style>
