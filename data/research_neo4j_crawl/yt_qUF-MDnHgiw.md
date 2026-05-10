# Transcript: https://www.youtube.com/watch?v=qUF-MDnHgiw

**Language:** English (auto-generated) (en) — auto-generated
**Snippets:** 579

---

**[00:09]** Welcome everyone. I hope you all are  
**[00:11]** excited for this next session. I see uh  
**[00:14]** folks joining us. So let's give them a  
**[00:17]** couple of uh seconds more today uh till  
**[00:20]** we have maybe a full house.  
**[00:24]** Okay, I think we have a good number of  
**[00:26]** folks join in so we can start. Once  
**[00:30]** again, welcome everyone. Uh we have with  
**[00:33]** us here today Tomas uh who is the  
**[00:36]** generative AI researcher at Neo 4G and  
**[00:39]** with his presentation on agentic memory.  
**[00:43]** So over to you Tomas.  
**[00:45]** >> Okay. So thanks uh for the introduction.  
**[00:49]** So as mentioned today I'm going to talk  
**[00:51]** about agentic memory but first I have a  
**[00:55]** little present for you. So like two  
**[00:58]** months ago me and Oscar finished a book  
**[01:01]** called essential graph and you can get  
**[01:04]** it for free at newj.com.  
**[01:07]** Hopefully uh you'll get the link pasted  
**[01:10]** in the chat as well.  
**[01:13]** So that's one little cookie for you  
**[01:15]** before we start. But now let's dive  
**[01:17]** right into the presentation.  
**[01:21]** So nowadays  
**[01:23]** AI models like uh it feels like you have  
**[01:28]** like a brilliant assistant but like  
**[01:30]** every time you start a new chat it  
**[01:32]** forgets everything right so that's kind  
**[01:35]** of the problem um that we're facing and  
**[01:39]** uh so basically like I said it's  
**[01:43]** basically a stateless AI so every new  
**[01:45]** interaction is day one so basically  
**[01:48]** every new chat or conversation you  
**[01:51]** uh basically the LLM has blank memory so  
**[01:54]** it doesn't remember anything from  
**[01:56]** previous conversation and such. So you  
**[01:59]** have to restate a lot of uh information  
**[02:03]** if you're doing the same flows for  
**[02:05]** example and then on the other side it's  
**[02:09]** also not remembering  
**[02:11]** user user preferences and such. So  
**[02:15]** basically like I said the LN does not  
**[02:18]** learn from interactions  
**[02:21]** and conversations with you and doesn't  
**[02:23]** tailored the answers to your uh spec  
**[02:29]** specifications but it's just like it's  
**[02:33]** like every every new conversation  
**[02:36]** basically an AI suffers amnesia forgets  
**[02:38]** everything and you have to restart from  
**[02:41]** scratch right and basically this is the  
**[02:44]** motivation for agentic memory  
**[02:48]** to enable uh a persistent layer of  
**[02:52]** context so that the L&M can remember  
**[02:54]** your preferences histories goals it for  
**[02:57]** example it can remember your job title  
**[03:00]** it knows like if you're the technical  
**[03:01]** person technical person non-technical  
**[03:04]** person so it can drive through  
**[03:06]** personalizations it can uh improve over  
**[03:09]** time by learning from your feedback  
**[03:11]** right and it can also help you work on  
**[03:15]** longer running multi-step projects,  
**[03:18]** right? And I feel like if like last year  
**[03:21]** was the year of AI agents, this year or  
**[03:25]** at least like the last six months is  
**[03:27]** basically a memory is where most of the  
**[03:29]** hype is happening, right? So let's now  
**[03:33]** dive right into the the next step. So  
**[03:37]** how I see it is basically on a high  
**[03:40]** level we have two types of memories. We  
**[03:43]** have long-term and short short-term  
**[03:45]** memories.  
**[03:47]** Short-term memory is basically as you  
**[03:50]** see uh it's like a current conversation  
**[03:53]** or the current session. It holds  
**[03:56]** immediate context. So it's basically the  
**[03:58]** current conversation with nowadays  
**[04:00]** basically  
**[04:02]** uh you you do a lot of tools  
**[04:06]** and then once it the memory just lasts  
**[04:09]** for the session and then restarts when  
**[04:11]** you start a new session right so that's  
**[04:14]** basically built into the LLMs because  
**[04:17]** they're like most of them are chat  
**[04:19]** models so you can just dump the short  
**[04:22]** memory into the LLM and it will work  
**[04:25]** whereas on the other side we have kind  
**[04:27]** of the more interesting it's the  
**[04:29]** long-term memory. So it's kind of the  
**[04:32]** knowledge base for the AI and it's uh  
**[04:36]** it's basically persistent right so it  
**[04:38]** it's it doesn't restart which with every  
**[04:41]** session and it stores like facts  
**[04:44]** experiences user preferences best  
**[04:47]** projects learn skills and such right so  
**[04:51]** this is basically the long-term memory  
**[04:53]** is what allows you to give persistent  
**[04:57]** context to the ll so that you don't have  
**[04:59]** to restate basically ally your  
**[05:02]** preferences or your job title or  
**[05:05]** whatever to the to the LLM every time so  
**[05:08]** that it it gives you better and more  
**[05:10]** accurate responses.  
**[05:12]** So let's look at the short shorter  
**[05:16]** memory first. So basically like I said  
**[05:18]** shortterm memory just holds  
**[05:21]** each conversation right  
**[05:24]** and nowadays it's not just input output  
**[05:28]** but we have LLM thinking we have tool  
**[05:31]** calls tool responses and like if you're  
**[05:34]** using for example cloth as you can see  
**[05:36]** in this screenshot as well  
**[05:40]** uh like one user input can have like 20  
**[05:44]** steps before the LLM responds. response  
**[05:47]** with u with a response, right?  
**[05:52]** uh and uh so but more mo more or less  
**[05:56]** like we have these four types of  
**[05:58]** messages that can happen in a  
**[06:00]** conversation or the session  
**[06:04]** and uh it's fairly simple to represent  
**[06:08]** that in a graph right so a user here  
**[06:11]** John has a session you can call it a  
**[06:14]** conversation or session depends on your  
**[06:16]** preferences and then each  
**[06:20]** session has a sequence of uh messages  
**[06:25]** that stores basically your conversation.  
**[06:28]** uh we can have like the user it usually  
**[06:31]** starts with the user message right if  
**[06:33]** you're using a thinking model we can  
**[06:35]** have a thinking step most of the time  
**[06:38]** nowadays there's a tool call and then  
**[06:40]** the LM response and there could be like  
**[06:43]** multiple user uh questions right it  
**[06:46]** doesn't have to be like here just five  
**[06:48]** it could be like 25 or 30 messages in a  
**[06:52]** sequence  
**[06:54]** and uh it's fairly straightforward that  
**[06:58]** a user can have multiple sessions and  
**[07:00]** then sessions have messages and  
**[07:03]** basically the retrieval is also fairly  
**[07:05]** simple.  
**[07:07]** You just need a session ID. You use the  
**[07:10]** session ID ID to retrieve the sequence  
**[07:12]** of messages and you basically you can  
**[07:15]** dump the whole uh message history into  
**[07:19]** the LLM and then the LLM takes care of  
**[07:21]** it. Right? So there's like no no  
**[07:23]** advanced retrieval or storage  
**[07:27]** uh patterns. You don't really need a lot  
**[07:30]** of prep-processing  
**[07:31]** or basically any preprocessing for that  
**[07:34]** matter.  
**[07:36]** And this is basically the short-term  
**[07:37]** memory that kind of stores your  
**[07:40]** conversations so that you can come back  
**[07:42]** to conversation at a later time if you  
**[07:44]** want. And basically all I feel like LM  
**[07:49]** providers have the this uh capability  
**[07:52]** built in right so it's nothing special  
**[07:54]** but I just wanted to start simple so  
**[07:56]** that you can see basically what's a  
**[07:59]** shortterm memory  
**[08:01]** and then now for the exciting part we  
**[08:04]** can have the long the the longterm  
**[08:07]** memory is basically where the magic  
**[08:09]** happens right and let's take a look at  
**[08:12]** it so  
**[08:14]** It's kind of interesting that we try to  
**[08:17]** copy humans like how does memory and  
**[08:21]** human being thinks how it works and try  
**[08:25]** to model that for LLMs. So basically as  
**[08:29]** far doing my research I've seen that  
**[08:32]** basically  
**[08:34]** on high level kind of three types of  
**[08:38]** memories  
**[08:40]** that you want to have for your LMS or AI  
**[08:43]** agents. The first one is the episodic  
**[08:45]** memory. So there's basically remembering  
**[08:49]** personal experiences and events. So it's  
**[08:51]** basically the memory from your point of  
**[08:53]** view.  
**[08:54]** So it's basically user specific memory.  
**[08:58]** And then we have semantic memory.  
**[08:59]** Semantic memory is basically storing  
**[09:01]** general knowledge and facts about the  
**[09:03]** word or if it's like in a business uh  
**[09:07]** domain or context then it's like storing  
**[09:10]** business knowledge and facts. And then  
**[09:13]** the third one is the so-called  
**[09:14]** procedural memory. So basically the  
**[09:16]** procedural memory  
**[09:19]** restores the information on how to  
**[09:22]** perform different skills, tasks and  
**[09:25]** actions.  
**[09:27]** So let's walk through these types of  
**[09:29]** memory so you'll get a better feel for  
**[09:32]** what what they are and how to implement  
**[09:34]** them. So the first one is the episotic  
**[09:37]** memory.  
**[09:39]** So as I mentioned it's uh basically  
**[09:43]** designed to store information about the  
**[09:46]** user. So basically the idea is that it's  
**[09:51]** it's it's those user specific  
**[09:54]** preferences, facts and p discuss past p  
**[09:57]** discussions to adapt or to be able to  
**[10:01]** personalize  
**[10:02]** uh  
**[10:05]** uh answers to the LLM but also to be  
**[10:08]** able to have like a longer term  
**[10:11]** relationship with your agent. So uh as I  
**[10:15]** mentioned it's mostly built to do the  
**[10:18]** dialogue with the user and so it kind of  
**[10:22]** creates like a user point of view within  
**[10:26]** let's say if you're talking in the  
**[10:27]** business context it creates like a user  
**[10:30]** point of view  
**[10:32]** of uh  
**[10:34]** of the business right so for example uh  
**[10:39]** it can it knows basically on the  
**[10:41]** projects you're working on it can know  
**[10:43]** your job title. It can know your  
**[10:44]** co-workers and then basically that helps  
**[10:49]** it to personalize  
**[10:51]** uh messages for you. So basically um as  
**[10:56]** I said  
**[10:58]** with episodic memory the idea is that  
**[11:01]** each user gets its own episodic memory  
**[11:03]** because it's user specific. Like I said  
**[11:05]** right the LLM learns facts about you and  
**[11:10]** the works that you're doing at the  
**[11:11]** company. So the source of the  
**[11:14]** information is mostly the dialogue that  
**[11:17]** you have with the LLM. It can also be  
**[11:20]** some like job titles and such that you  
**[11:23]** can provide to the LLM. But from what  
**[11:27]** I've seen, the most um the the most  
**[11:31]** relevant data source is the  
**[11:35]** uh conversation with the LLM where you  
**[11:37]** can basically basically from the LLM  
**[11:40]** learns from you asking questions like  
**[11:42]** what are what are you interested in,  
**[11:45]** what what needs your attention and such,  
**[11:48]** right? Then the LLM kind of learns more  
**[11:52]** about basically what do you do at the  
**[11:54]** company, what are your preferences and  
**[11:57]** such.  
**[11:58]** So uh I probably you've seen like such  
**[12:02]** data model. So on the right side we  
**[12:05]** still have the same shortterm memory  
**[12:07]** that we had before. So, a session with  
**[12:10]** messages,  
**[12:12]** but we introduce like a post-processing  
**[12:15]** step where we  
**[12:18]** now there's not like a one standard data  
**[12:20]** model for episodic memory. There's a  
**[12:22]** bunch of them, but a lot of them  
**[12:25]** involves introducing like events. So you  
**[12:28]** can have what like events like a sales  
**[12:30]** meeting with a company and then we do  
**[12:33]** like information position which like two  
**[12:37]** years ago like yeah two years ago it was  
**[12:40]** most like selecting triples. So it could  
**[12:42]** be like the sales meeting with a  
**[12:45]** specific company involves that company  
**[12:48]** and also involves like a you uh a person  
**[12:51]** on the other side  
**[12:54]** and who's a decision maker let's say for  
**[12:56]** this deal  
**[12:58]** uh so that that will be kind of triple  
**[13:00]** but what we've seen I would say in the  
**[13:03]** last year good year or so that basically  
**[13:05]** we've moved away from extracting simple  
**[13:08]** triplets  
**[13:10]** to extracting let's say quintup ers  
**[13:12]** because what's really  
**[13:15]** uh been important that we we have to we  
**[13:18]** must not neglect the temporal component  
**[13:22]** of the information as well right because  
**[13:23]** with triples  
**[13:25]** uh there's usually no temporal component  
**[13:28]** time information right so it's really  
**[13:31]** important to know when this deal is  
**[13:33]** going to happen how much time we have to  
**[13:36]** prepare for it like how long John is  
**[13:40]** working at that specific company, right?  
**[13:43]** Because over time you can accumulate a  
**[13:46]** bunch of information and then things  
**[13:48]** change over time, right? And you want to  
**[13:50]** be able to track information um that's  
**[13:54]** changing. And then the other thing, the  
**[13:57]** second thing that I've kind of also  
**[13:59]** noticed is that instead of just  
**[14:02]** extracting triples like subject,  
**[14:05]** predicate, object, right, there's also  
**[14:08]** now a trend of extracting  
**[14:11]** a description. So like more like a free  
**[14:14]** for text property for each of the nodes  
**[14:17]** because when you're doing a triplet  
**[14:21]** extraction,  
**[14:23]** it's sometimes it's hard to capture like  
**[14:26]** some nuanced information using uh  
**[14:29]** triplets, right? So the idea is then to  
**[14:31]** allow the island to also have like a  
**[14:33]** free form text where it can store that u  
**[14:37]** more nuanced information for entities  
**[14:40]** and such, right?  
**[14:42]** And uh it's kind of interesting that I  
**[14:46]** also wanted to mention that what I've  
**[14:48]** seen that one problem with episodic  
**[14:52]** memory is that u when users are  
**[14:55]** interacting with it like they can input  
**[14:57]** sensitive data. So that can be a problem  
**[14:59]** as well. You have to kind of deal with  
**[15:01]** it right because users can put a lot of  
**[15:04]** sensitive information and like do you  
**[15:06]** want to store all that in your graph or  
**[15:08]** not? I don't know just yet. But that's  
**[15:10]** like one thing to keep in mind when  
**[15:12]** you're extracting information from  
**[15:14]** conversations. But let's move into it.  
**[15:16]** But  
**[15:18]** what's kind of also now  
**[15:21]** a lot of people are doing this. So now  
**[15:24]** because you can accumulate like I said  
**[15:26]** you can accumulate a lot of information  
**[15:28]** over time using this extraction and you  
**[15:31]** can also because you have the  
**[15:34]** descriptions the phone for text that  
**[15:36]** you're also extracting  
**[15:38]** you can accumulate a lot of information.  
**[15:40]** So then basically a lot of these uh  
**[15:45]** agentic memory frameworks introduce like  
**[15:47]** summary steps. So it's kind of like when  
**[15:50]** humans go to sleep, right? They kind of  
**[15:53]** congest and process the information that  
**[15:55]** they've seen during the day and it's  
**[15:59]** kind of similar with the agents agentic  
**[16:02]** memory. So basically over time you can  
**[16:05]** start to create so basically let's say  
**[16:08]** John Davis can appear in a lot of  
**[16:11]** conversations. So now you want to  
**[16:13]** congest that information right so that  
**[16:15]** you have like a more congested and like  
**[16:18]** smaller token size information about  
**[16:20]** John in one place instead of having to  
**[16:24]** search through 20 conversations to find  
**[16:27]** all information about John.  
**[16:30]** So uh we it's kind of like introducing  
**[16:34]** sleep. So it's like a batch processing u  
**[16:37]** job that you do like for example I've  
**[16:40]** just seen that cloth introduced memory  
**[16:43]** and they do summarization once every 24  
**[16:46]** hours for I don't I don't know exactly  
**[16:50]** what they're summarizing just yet but I  
**[16:53]** just know that they basically do this  
**[16:55]** batch summarization once every 24 hours.  
**[16:59]** So you kind of congest information,  
**[17:01]** right? Because when you present  
**[17:03]** information to the LLM from the memory,  
**[17:05]** you want it in a nice congested way so  
**[17:08]** that you do not overwhelm  
**[17:10]** the LLM and give it a lot of tokens.  
**[17:14]** So that's kind of for the episodic  
**[17:16]** memory. Like I said, the idea is that  
**[17:18]** you build graphs from conversational  
**[17:22]** dialogues and each user gets it gets its  
**[17:26]** own episodic memory, right? so that we  
**[17:29]** can learn pref preferences for each  
**[17:32]** specific user. And then the second type  
**[17:35]** of memory is a so-called semantic  
**[17:37]** memory. So semantic memory in a business  
**[17:40]** context is basically  
**[17:43]** like it's a single graph that contains  
**[17:46]** facts about the company. So it allows  
**[17:50]** company or employees to find companywide  
**[17:53]** information like Wikipedia or like  
**[17:58]** dandom user databases and such. So I see  
**[18:02]** like semantic memory is basically kind  
**[18:04]** of the rack and graph rack  
**[18:06]** approaches that we've talking about  
**[18:09]** where basically you instead of building  
**[18:13]** memory from text like conversations  
**[18:16]** you're building memory from documents  
**[18:18]** and that's basically  
**[18:20]** what all of us have been doing for the  
**[18:22]** last two years. So you take the  
**[18:25]** documents that are describing like  
**[18:27]** companies  
**[18:28]** uh processes, companies policies and  
**[18:33]** maybe also something else and you try to  
**[18:36]** build like a knowledge layer around it.  
**[18:40]** Right? So it's basically a companywide  
**[18:43]** single source of truth for the employees  
**[18:47]** and it's built on top of the  
**[18:49]** documentation or other knowledge bases  
**[18:52]** right because I feel like that people  
**[18:54]** kind of forget that that memory or like  
**[18:58]** agents only work on text but you can  
**[19:01]** also use other knowledge bases like user  
**[19:04]** databases CRM to build your foundational  
**[19:08]** knowledge layer as well.  
**[19:10]** So as for the data model, it's fairly  
**[19:12]** sim similar to the episodic one. It's  
**[19:15]** just that instead of building  
**[19:18]** information on top of conversations,  
**[19:21]** we're building information on top of  
**[19:23]** documents and chunks, right? But other  
**[19:26]** than that, it the idea is the same.  
**[19:29]** We're still kind of extracting  
**[19:32]** I call them quintuples. So it's like  
**[19:34]** triples but with additional temporal  
**[19:37]** component. and the description.  
**[19:42]** And since basically it's a single graph  
**[19:45]** for all the users, right? You might want  
**[19:49]** to introduce some role based access  
**[19:53]** because maybe the CEO can see more  
**[19:56]** things than I don't know a janitor for  
**[19:59]** example, right? But then like I said the  
**[20:02]** idea is that it's like one companywide  
**[20:05]** graph that that covers the information  
**[20:09]** about the company  
**[20:11]** and what we've also seen is the emerging  
**[20:14]** schema trend. So because like building  
**[20:16]** graphs from the documents is hard and  
**[20:18]** then building uh like defining schema is  
**[20:21]** also like a labor intensive work. So  
**[20:25]** what we've seen is basically that  
**[20:28]** building this like semantic memory  
**[20:31]** layers is basically an iterative  
**[20:33]** process. So you take a like a sample of  
**[20:35]** your documents. You you use the LLM to  
**[20:38]** produce like a sample schema. You have  
**[20:41]** the human in the loop where uh you you  
**[20:44]** basically refine the schema, look at it  
**[20:47]** if it makes sense or not, what's  
**[20:49]** important for the company and what's  
**[20:51]** not. Maybe find some duplicates.  
**[20:55]** And then you have like the finalized  
**[20:59]** maybe like let's say it's not the  
**[21:00]** finalized but it's like the first  
**[21:02]** version that you can use for processing  
**[21:06]** your documents right so like I said uh  
**[21:09]** what we've seen is that basically we use  
**[21:12]** LLMs  
**[21:14]** also for like defining the schema so  
**[21:16]** basically LLMs are used at every step we  
**[21:19]** use them to help us learn about what's  
**[21:22]** what's the information in a document we  
**[21:25]** and use the LMS to extract the  
**[21:26]** information. And finally, we also use  
**[21:28]** LMS to for the DT.  
**[21:33]** And then the last type of memory is the  
**[21:36]** procedure procedural memory. The  
**[21:39]** precision memory is basically  
**[21:43]** it it learns I I feel like again it's it  
**[21:47]** it should be like a companywide  
**[21:50]** but it's basically it's it's  
**[21:53]** so basically the procedural memory  
**[21:55]** focuses on procedural procedures right  
**[21:58]** so basically  
**[22:01]** you can have like a companywide graph of  
**[22:04]** guidelines how to build specific repos  
**[22:07]** or like how specific matrix are  
**[22:10]** calculated  
**[22:11]** and such. So, uh basically  
**[22:15]** you can like if you ask the LM to build  
**[22:18]** like a specific report,  
**[22:20]** you should get the same report with the  
**[22:23]** same definitions every time, right? And  
**[22:26]** u just like two three weeks ago maybe.  
**[22:31]** Yeah. So like I said  
**[22:34]** the uh the idea behind procedural memory  
**[22:38]** is to identify like recurring tasks,  
**[22:42]** prompt formers and workflows and then  
**[22:45]** store them in the graph so that the LLM  
**[22:48]** can follow prescribed templates on how  
**[22:51]** to build and solve user requests  
**[22:56]** and uh because of that it it helps the  
**[23:00]** LLM to create like um or like to create  
**[23:03]** like a sense of flow friction with the  
**[23:05]** user. So because the user feels like  
**[23:10]** the LM understands how to create  
**[23:13]** specific reports solves different tasks  
**[23:16]** and it does them in a more um  
**[23:21]** consistent way, right? Because like if  
**[23:23]** you want to if you have to do like a  
**[23:25]** weekly report,  
**[23:28]** you would want to have like the same  
**[23:29]** template done like every week, right?  
**[23:32]** Without having to really explain what  
**[23:34]** the template looks like and uh like I  
**[23:37]** mentioned just like two weeks ago  
**[23:41]** basically cloud skills were were  
**[23:43]** introduced. So maybe three four weeks  
**[23:45]** and the idea is kind of the same. Uh so  
**[23:49]** basically the cloud skills are like file  
**[23:51]** based  
**[23:52]** procedural memory where you give the LLM  
**[23:56]** at the runtime the ability to search for  
**[23:59]** specific usage patterns or workflows and  
**[24:02]** then um it can search that information  
**[24:05]** and use that to better  
**[24:08]** uh create a soft test that and uh  
**[24:13]** basically you can easily uh model that  
**[24:18]** the cloud skills approach for example in  
**[24:21]** uh Neo forj right so you would have like  
**[24:24]** uh  
**[24:26]** several levels of uh repos right so one  
**[24:30]** would be like like okay we have like  
**[24:34]** business uh reports and then it's like  
**[24:37]** okay by which department we can have  
**[24:39]** like operations report HR reports and  
**[24:42]** for example we can have operations KPI  
**[24:44]** dashboard and then  
**[24:47]** The operations KPI dashboard can contain  
**[24:50]** like the prompt or the templates that  
**[24:52]** could be ingested or that the that can  
**[24:55]** inform the LM how to perform such uh  
**[24:58]** dashboards or the reports. And then we  
**[25:00]** can also have um for examples for  
**[25:03]** specific metrics  
**[25:05]** uh definitions how to how to generate  
**[25:11]** them or how to calculate them.  
**[25:14]** So that's uh that those are the three  
**[25:18]** types of memory. I know that it's kind  
**[25:21]** of high level and I didn't give you a  
**[25:23]** lot of actionable items which I'm sorry  
**[25:27]** but I wanted to give you that I wanted  
**[25:29]** to show you that a lot of these memories  
**[25:32]** are available through existing uh  
**[25:37]** integrations with aentic memory  
**[25:39]** frameworks. So for example, Cogni, M0  
**[25:42]** and Zap, they all they all have the  
**[25:44]** option to use Neo forj under the hood.  
**[25:45]** So if you want to go and explore like  
**[25:49]** what are some aentic frameworks doing, I  
**[25:52]** would suggest you use the open source  
**[25:56]** versions of the frameworks and then you  
**[25:58]** can go and see exactly what happens and  
**[26:01]** learn more from that. We also have some  
**[26:04]** MCP server from Neo Forj that you can  
**[26:06]** also take a look.  
**[26:08]** So like I mentioned most of these uh  
**[26:12]** frameworks focus on u basically I think  
**[26:17]** m and zap have a bigger focus on  
**[26:19]** episodic memory where they're building  
**[26:21]** graphs from conversation and cogn  
**[26:24]** somewhere in the middle.  
**[26:27]** So uh but it should be like a good start  
**[26:30]** for you to get started with implementing  
**[26:34]** agentic memory into your agentic  
**[26:37]** applications.  
**[26:39]** So uh that's it for my talk. Thanks for  
**[26:42]** listening. And now maybe because we have  
**[26:45]** two minutes maybe one question.  
**[26:53]** >> Thank you so much Tomas. wonderful uh  
**[26:55]** presentation and yes we do have a minute  
**[26:59]** to two so if there are any questions um  
**[27:04]** you'd like to put in please do so on the  
**[27:08]** session chat and yeah Tomas you could  
**[27:11]** look at it too and you know respond to  
**[27:13]** them  
**[27:14]** >> uh okay then I'll respond in the chat  
**[27:22]** Okay.  
**[27:31]** >> And um thank you everybody for joining.  
**[27:35]** We have posted the postevent uh feedback  
**[27:38]** survey for this particular session. So  
**[27:41]** uh please do make sure that you are  
**[27:43]** submitting that survey uh before you  
**[27:46]** leave and join your next uh session.  
**[27:50]** >> Okay.  
**[27:52]** We are good.  
**[27:54]** >> Yes. Wonderful. Thank you so much. Uh  
**[27:56]** once again guys, uh please join the next  
**[27:59]** session on your schedule and again don't  
**[28:02]** forget to uh complete the feedback.  
**[28:04]** Bye-bye. Have a great rest of the day.  
**[28:06]** >> Bye.  