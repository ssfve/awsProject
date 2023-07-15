import Vue from 'vue'
import Router from 'vue-router'
import Notification from '@/components/home/Notification'


Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      name: 'Notification',
      component: Notification
    }
  ]
})
