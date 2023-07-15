<template>
    <div class="notification container">
        <form @submit.prevent="sendMessage" class="card-panel">
            <h3 class="center-align blue-text">Post New Notification</h3>
            <div class="field">
                <span>EventId</span><input type="text" name="eventId" v-model="eventId">
            </div>
            <br/>
            <div class="field">
                <span>Message</span>
                <textarea v-model="englishTxt"></textarea>
            </div>
            <br/>
            <p v-if="feedback" class="red-text center">{{ feedback }}</p>
            <br/>
            <div class="field center">
                <button class="btn light-blue">Send Message</button>
            </div>
        </form>
    </div>
</template>

<script>
import { API } from '@aws-amplify/api'
import slugify from 'slugify'
import { Auth } from '@aws-amplify/auth';

export default {
    name: 'SendMessage',
    data() {
        return {
            apiName: 'MLNApp',
            path: '/announcement',
            eventId: null,
            englishTxt: null,
            feedback: null,
            username: null
        }
    },
    methods: {
        async sendMessage(){
            let results = await Auth.currentUserInfo()
            console.log(`Done: ${JSON.stringify(results.username)}`)
            this.username = results.username
            console.log(this.username)

            if(this.eventId && this.englishTxt) {
                this.slug = slugify(this.englishTxt, {
                replacement: '-',
                remove: /[$*_+~.()'"!\-:@]/g,
                lower: true
                }),
                await API.post(this.apiName, this.path, {body:{
                    eventId: this.eventId,
                    englishTxt: this.englishTxt,
                }}).then(response => {
                  this.feedback = "Successfully posted the message";
                  this.eventId = this.englishTxt = '';
                  event.target.reset();
                }).catch(err =>{
                    console.log(err)
                })
                }
                 else {
                this.feedback = "You must enter all fields";
            }
        }
    }
}
</script>

<style>
.add-notification{
    max-width: 200px;
    margin-top: 60px;
}
.add-notification h2{
    font-size: 2.4em;
}
.add-notification .field{
    margin-bottom: 16px;
    margin-top: 40px;
}
</style>