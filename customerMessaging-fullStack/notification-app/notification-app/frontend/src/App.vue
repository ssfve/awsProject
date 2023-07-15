<template>
	<div id="app">
    	<Header />
		<amplify-authenticator class="center">
		<div id="amplify-signout">
			<amplify-sign-out></amplify-sign-out>
		</div>
    	<router-view />
		</amplify-authenticator>
    	<Footer />
  	</div>
</template>

<script>
import Header from '@/components/layout/Header'
import Body from './components/layout/Body';
import Footer from '@/components/layout/Footer'

export default {
	name: 'App',
	components: {
			Header,
			Body,
    	    Footer
	}
}
</script>

<style>
#app {
  margin: 5px auto;
  border-top: 10px;
}
#amplify-signout {
  width: 100px;
  margin: 5px auto;
}
</style>
