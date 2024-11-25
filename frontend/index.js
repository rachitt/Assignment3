document.getElementById('displaytext').style.display = 'none';

async function searchPhoto() {
  const apigClient = apigClientFactory.newClient();
  const user_message = document.getElementById('note-textarea').value;

  const params = { q: user_message };
  const body = {};
  const additionalParams = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  try {
    const res = await apigClient.searchGet(params, body, additionalParams);
    const resp_data = res.data;
    const length_of_response = resp_data.length;

    if (length_of_response === 0) {
      document.getElementById('displaytext').innerHTML =
        'Sorry could not find the image. Try again!';
      document.getElementById('displaytext').style.display = 'block';
    }
    else {
      const imgContainer = document.getElementById('img-container');
      const images = imgContainer.getElementsByTagName('img');
      while (images.length > 0) {
        images[0].parentNode.removeChild(images[0]);
      }
      document.getElementById('displaytext').innerHTML = 'Images returned are:';
      resp_data.keys.forEach((obj) => {
          const img = new Image();
          img.src = `https://image-search-data.s3.us-east-1.amazonaws.com/${obj}`;
          img.setAttribute('class', 'banner-img');
          img.setAttribute('alt', 'effy');
          imgContainer.appendChild(img);
      });
      document.getElementById('displaytext').style.display = 'block';
    }
    document.getElementById('note-textarea').value = '';
  } catch (err) {
    console.error('Error:', err);
    document.getElementById('displaytext').innerHTML =
      'An error occurred. Please try again later.';
    document.getElementById('displaytext').style.display = 'block';
  }
}

function getBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      let encoded = reader.result.replace(/^data:(.*;base64,)?/, '');
      if (encoded.length % 4 > 0) {
        encoded += '='.repeat(4 - (encoded.length % 4));
      }
      resolve(encoded);
    };
    reader.onerror = (error) => reject(error);
  });
}

async function uploadPhoto() {
  const fileInput = document.getElementById('file_path');
  const file = fileInput.files[0];
  const customLabels = document.getElementById('note_customtag').value;
  const params = {
    bucket: 'image-search-data',
    key: `${Date.now()}-${file.name}`
  };

  try {
    const data = await getBase64(file);
    const apigClient = apigClientFactory.newClient();

    const file_type = `${file.type};base64`;
    const additionalParams = {
      headers: {
        'Accept': 'image/*',
        'Content-Type': file_type,
        'x-amz-meta-customlabels': customLabels
      }
    };

    const body = data;
    const res = await apigClient.uploadBucketKeyPut(params, body, additionalParams);
    if (res.status === 200) {
      document.getElementById('uploadText').innerHTML =
        'Your image is uploaded successfully!';
      document.getElementById('uploadText').style.display = 'block';
      fileInput.value = '';
    }
  } catch (err) {
    console.error('Error uploading photo:', err);
    document.getElementById('uploadText').innerHTML =
      'Error uploading photo. Please try again later.';
    document.getElementById('uploadText').style.display = 'block';
  }
}