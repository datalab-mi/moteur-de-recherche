async function upload(meta, file) {
  //for (var i = 0; i < files.length; i++) {
    //var file = files[i];
  const formData = new FormData();
  console.log('upload :')
  console.log(file)
  const filename = file.name
  formData.append('file', file);

  meta.forEach(item => formData.append(item.key, JSON.stringify(item.value)));

  const upload = await fetch(`/api/admin/${filename}`, {
      method: 'PUT',
      body: formData
      });

  if (upload.ok) {
    return upload.status
  } else {
    console.log('error')
    throw new Error('Oups');
  }
}

async function index(index_name, filename, method) {
    let statusOK;
    // handle status of the http request
    if (method == 'PUT') {
      statusOK = (s) => s.status
    } else if (method == 'DELETE') {
      statusOK = (s) => (s.ok || s.status == 404)
    }
    // Make the  http request
    const index = await fetch(`/api/admin/${index_name}/_doc/${filename}`,
      {method: method});
		if (statusOK(index)) {
			return index.status
		} else {
      console.log('error')
			throw new Error('Oups');
		}
}

export { index, upload };
