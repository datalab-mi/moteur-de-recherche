<script>
import { searchList, searchResults, index_name } from '../components/stores.js';
import { onMount } from 'svelte';

import ResultItem from '../components/ResultItem.svelte';
import VirtualList from '../components/VirtualList.svelte';
let start;
let end;
let items
let height = '90%';

$: {
	let i = 0;
	items = $searchResults.hits
	console.log('items : ')
	console.log(items)
	for (const hits of $searchResults.hits){
		if (hits._score < $searchResults.threshold){
			break
		}
		i += 1
	}
	items.splice(i, 0, "bar")
}

</script>


{#if searchResults}
	<div class='result-list'>
	<p>{start}-{end}</p>
		<VirtualList {items} {height} bind:start bind:end let:item>
			{#if  item === "bar"}
				<div class="bar">
					<p>Le document que vous recherchez a peu de chance de se trouver en dessous de cette bande. Nous vous recommandons de contacter  <a href="mailto://iga@interieur.gouv.fr?subject=Demande_de_consultation">[iga@interieur.gouv.fr]</a></p>
				</div>
			{:else}
				<ResultItem {...item}/>
			{/if}
		</VirtualList>
	</div>
{/if}

<style>
	.result-list {
		width: 100%;
		border: 1px solid #aaa;
		border-radius: 4px;
		box-shadow: 2px 2px 8px rgba(255,0,0,1);
		padding: 1em;
		margin: 0 0 1em 0;
		height: calc(200vh - 15em);
		min-height: 200px;
	}
.bar {
	border: 1px solid #aaa;
	border-radius: 2px;
	box-shadow: 2px 2px 8px rgba(0,255,0,1);
	padding: 1em;
	margin: 1em 1em 1em 1em;
}
</style>
