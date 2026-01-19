(async () => {
    const module = await import(` http://10.242.59.159:5000/app.js`); // Change Your API
    module.initChat(); 
})();


