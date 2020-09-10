<script>

    import PutItem from './PutItem.svelte'
    import { index_name } from './stores.js';
    import {upload, index } from  './utils.js'

    export let meta;
    export let cssClass = 'base';

    export let readonly = false;
    export let required = true;

</script>

<section class="{cssClass}-item">

  <div class="mb-4">
    {#each meta as {key, type, placeholder, value, innerHtml, readonly, highlight}, i }
      {#if (key == "title") || (key == "titre")}
        <h2>
          <textarea class='{cssClass}-title' type='text' bind:value={value} {placeholder} {readonly}/>
        </h2>

        <slot name="highlight">
        </slot>

      <br>
      {:else if type == "text"}
        <label> {@html innerHtml}
          <input type='text' bind:value={value} {placeholder} {readonly}/>
        </label>

      {:else if type == "textarea"}
      <label> {@html innerHtml}
        {#if highlight}
          <p> &laquo; {@html value} &raquo; </p>
        {:else}
            <textarea bind:value={value} {placeholder} {readonly}/>
        {/if}
      </label>

      {:else if type == "date"}
        <br>
        <label> {@html innerHtml}
          {#if required}
            <input type='date' bind:value={value} {placeholder} {readonly} required />
          {:else}
            <input type='date' bind:value={value} {placeholder} {readonly}/>
          {/if}
        </label>
      {/if}
    {/each}
  </div>

  <div class="flex justify-between">

    <slot name="button">
    </slot>

    <slot name="score">
    </slot>

  </div>

</section>

<style>
  .result-item {
    border: 1px solid #aaa;
    border-radius: 2px;
    box-shadow: 2px 2px 8px rgba(0,0,255,1);
    padding: 1em;
    margin: 1em 1em 1em 1em;
  }
	.base-item {
		width: 100%;
		border: 1px solid #aaa;
		border-radius: 4px;
		box-shadow: 2px 2px 8px rgba(0,0,0,1);
		padding: 1em;
		margin: 0 0 1em 0;
	}

  input,textarea {
    border:none;
    width: 90%;
    resize: none;
    vertical-align: top;

   }


 .base-title {
	 font-weight: bold;
	 margin: 0;
	 padding: 0;
 }

 .result-title {
  color: blue;
  font-weight: bold;
  margin: 0;
  padding: 0;
 }
</style>
