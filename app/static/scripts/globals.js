$(window).ready(() => {});

const getCookie = (name) => {
	let cookieValue = null;
	if (document.cookie && document.cookie !== '') {
		const cookies = document.cookie.split(';');
		for (const element of cookies) {
			const cookie = element.trim();
			if (cookie.substring(0,name.length + 1) === (name + '=')) {
				cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
				break;
			}
		}
	}
	return cookieValue;
};

const downloadFile = (url, filename) => {
	let a = document.createElement("a");
	a.href = url;
	a.download = filename;
	a.style.display = "none";
	document.body.appendChild(a);
	a.click();
	document.body.removeChild(a);
};

const getFormData = (form) => {
	let data = {};
	$(form).serializeArray().forEach((item) => {
		data[item.name] = item.value;
	});
	return data;
};
