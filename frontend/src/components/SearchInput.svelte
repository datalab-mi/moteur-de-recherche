<script>
  export let innerHtml = "";
  export let style = "";
  export let placeholder = "";
  export let label = "";
  export let description = "";
  export let query = "azerty";
  export let type = "text";

  const handleInput = e => {
    // in here, you can switch on type and implement
    // whatever behaviour you need
    query = type.match(/^(number|range)$/)
      ? +e.target.value
      : e.target.value;
  };

</script>


<div class={style}>
  <label> {@html innerHtml}
    <input {type} value={query} {placeholder} on:input={handleInput}
      class="bg-white focus:outline-none focus:shadow-outline border border-gray-300 rounded-lg py-2 px-4 block w-full appearance-none leading-normal">
  </label>
</div>
