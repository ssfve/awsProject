// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import App from './App'
import router from './router'

import '@aws-amplify/ui-vue';
import Amplify from '@aws-amplify/core';
import { Auth } from '@aws-amplify/auth';
import awsmobile from './aws-exports';

Amplify.configure(awsmobile);

Auth.configure(awsmobile)

Vue.config.productionTip = false

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  components: { App },
  template: '<App/>'
})
