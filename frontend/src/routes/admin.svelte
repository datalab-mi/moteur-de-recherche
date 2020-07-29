<svelte:head>
	<title>Admin</title>
</svelte:head>

<script>
	import { onMount } from 'svelte';
	import Reindex from '../components/Reindex.svelte';
	import NewItem from '../components/NewItem.svelte';

</script>

<div>
	<h1>Ajout d'un nouveau document dans le moteur</h1>
	<br>
	<p>Renseignez des champs et selectionnez un fichier. Le document va être indexé
	automatiquement dans le moteur, il est inutile de reconstruire l'index Elasticsearch.</p>
	<NewItem />
</div>

<hr>

<div>
	<h1>Reconstruction de l'index Elasticsearch</h1>
	<br>
	<p>Cette action peut prendre du temps car tous les documents vont être réindexés.
	Quand la liste des synonymes ou que la manière d'analyser les documents changent, il faut réindexer. </p>
	<Reindex />
</div>


<style>
	h1 {
	    font-size: 2rem;
	}
	h2 {
	    font-size: 1.5rem;
	    padding-left: 20px;
	}
	hr {
	  display: block;
	  margin-top: 0.5em;
	  margin-bottom: 0.5em;
	  margin-left: auto;
	  margin-right: auto;
	  border-style: inset;
	  border-width: 1px;
	}
</style>
