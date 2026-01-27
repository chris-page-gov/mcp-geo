import App from "./App.svelte";

const app = new App({
  target: document.getElementById("app")
});

const bootScreen = document.getElementById("boot-screen");
if (bootScreen) {
  bootScreen.remove();
}

export default app;
