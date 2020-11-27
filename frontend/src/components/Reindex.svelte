<script>
import { index_name, isReindex } from './stores.js';

let promise;

async function ReIndex() {
		const res = await fetch(`/api/admin/${$index_name}/reindex`);
		const text = await res.text();

		if (res.ok) {
      $isReindex = false
			return text;
		} else {
			var win = window.open("", "Error", "toolbar=no,location=no,directories=no,status=no,menubar=no,scrollbars=yes,resizable=yestop="+(screen.height)+",left="+(screen.width));
			win.document.body.innerHTML = text;

			throw new Error(text);
		}
	}


	function handleIndex() {
    $isReindex = true
		promise = ReIndex()


	}
</script>



	<div>
    <button on:click={handleIndex} class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded inline-flex items-center">

    {#if $isReindex}
      <svg id="spinner" class="fill-current w-4 h-4 mr-2"  xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M14.66 15.66A8 8 0 1 1 17 10h-2a6 6 0 1 0-1.76 4.24l1.42 1.42zM12 10h8l-4 4-4-4z"/></svg>
    {:else}
      <svg class="fill-current w-4 h-4 mr-2"  xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M14.66 15.66A8 8 0 1 1 17 10h-2a6 6 0 1 0-1.76 4.24l1.42 1.42zM12 10h8l-4 4-4-4z"/></svg>
    {/if}

      <span>Réindexation</span>
    </button>
  </div>

<!-- svelte-ignore empty-block -->
{#await promise}
{:catch error}
<p style="color:red">Error</p>
<!-- <iframe srcdoc={error.message} height="300">
</iframe> -->
{/await}
<style>
#spinner {
  transition-property: transform;
  animation-name: svelte-spinner_infinite-spin;
  animation-duration: 750ms;
  animation-iteration-count: infinite;
  animation-timing-function: linear;
}
@keyframes svelte-spinner_infinite-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
