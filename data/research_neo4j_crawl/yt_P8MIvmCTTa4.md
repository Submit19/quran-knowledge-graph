# Transcript: https://www.youtube.com/watch?v=P8MIvmCTTa4

**Language:** English (auto-generated) (en) — auto-generated
**Snippets:** 427

---

**[00:08]** Hello. Hello everyone. Uh thanks uh for  
**[00:12]** that. Uh welcome once again to nodes.  
**[00:14]** Hope you all are having fantastic time  
**[00:16]** on the sessions. Um so uh let me go  
**[00:19]** ahead and quickly give a quick uh intro  
**[00:21]** about me. Uh I'm Fazel. Uh I'm an AI  
**[00:26]** engineer working at UNICES. uh I'm a  
**[00:28]** person who learn and uh grew with the  
**[00:31]** tech uh communities. Uh I always like to  
**[00:34]** come back and continuously uh contribute  
**[00:37]** uh especially in the AI space in one of  
**[00:39]** the other ways. Uh I also love taking  
**[00:41]** part in hackathons and I have  
**[00:43]** participated and won in some of the  
**[00:45]** national and international hackathons.  
**[00:47]** Uh I'm also a Bishnner fellow. I had  
**[00:50]** completed the fellowship.  
**[00:53]** So all right uh before we start with  
**[00:56]** today's session on the memory uh let me  
**[01:00]** start with uh narrating a short story  
**[01:03]** about uh Johnson. So uh you can just see  
**[01:07]** in the p uh it's like a comic fashion.  
**[01:09]** So he's part of the support team. Uh he  
**[01:12]** uses agent to basically um help him with  
**[01:15]** the task. uh let's say like uh it's just  
**[01:19]** week one and uh he feeds the LLM with  
**[01:22]** the tasks goals and road map and the A  
**[01:25]** models basically start understanding  
**[01:28]** this task which provides the adaptive  
**[01:30]** responses to his task and as weeks pass  
**[01:33]** by Johnson is uh really happy using the  
**[01:36]** model uh it becomes his uh super intern  
**[01:40]** and uh slowly slowly the context window  
**[01:42]** starts uh overflowing and one fine day  
**[01:46]** when Johnson asks uh the model uh about  
**[01:51]** his product and his road map, it starts  
**[01:54]** uh telling like hey I'm your new uh  
**[01:57]** assistant and how can I uh help you? So  
**[02:01]** you can see that uh it could not able to  
**[02:03]** recall the conversations after a long  
**[02:05]** time uh it had with Johnson. So like  
**[02:08]** Johnson is puzzled and he thought uh it  
**[02:11]** could learn and remember everything  
**[02:12]** about uh his work but it actually didn't  
**[02:16]** and that brings us to the concept of  
**[02:19]** memory in the assistance. So we'll  
**[02:22]** discuss on Neoforj as a graph uh  
**[02:25]** narrative memory layer. So our agents  
**[02:28]** don't just answer questions but actually  
**[02:31]** remember your context as it evolves. Um  
**[02:35]** moving forward. So this will be our  
**[02:37]** agenda for today. Uh we'll just see uh  
**[02:40]** what uh actually uh the AI uh remembers  
**[02:44]** and what we expected to remember and the  
**[02:48]** uh difference between what and how human  
**[02:51]** brain stores these uh conversations and  
**[02:53]** how AI memory stores them. Um the AI  
**[02:56]** memory at the context window and what  
**[02:59]** memory really means for these agents. uh  
**[03:02]** how the traditional um memory systems  
**[03:04]** fail and why we we need a graph uh kind  
**[03:08]** of a knowledge graph uh for storing  
**[03:11]** these memories and some of the failure  
**[03:13]** stories as well as the benefits uh of  
**[03:17]** persistent evolving and reliable systems  
**[03:20]** and we'll have the closing thoughts. So  
**[03:24]** the first thing um what's the actual  
**[03:27]** expectations from the user and what are  
**[03:31]** real and what's happening in reality. Um  
**[03:34]** so we as a humans we always have this  
**[03:36]** expectations that uh agents are smarter  
**[03:39]** and it knows uh uh some of our  
**[03:42]** information like our name or history and  
**[03:43]** our promises. It knows our preferences.  
**[03:46]** But uh in reality uh most of the LLMs uh  
**[03:50]** often ask these uh repetitive questions  
**[03:52]** for the 10th or the 100th time and I'm  
**[03:55]** sure most of you will agree for this uh  
**[03:57]** annoying questions as well. Um so most  
**[03:59]** of the agents that we see today are  
**[04:01]** actually uh stateless. So they live  
**[04:03]** inside a context window and it dies when  
**[04:08]** the context window closes. So it keeps  
**[04:11]** your context only till the session and  
**[04:14]** uh only till the session last and and it  
**[04:17]** starts from scratch from zero when the  
**[04:19]** new sessions begins. So that's the  
**[04:22]** actual reality in in the case of today's  
**[04:25]** uh agents and assistants. So the memory  
**[04:28]** actually ends at the context window and  
**[04:32]** uh if you inspect lot of uh the  
**[04:34]** production grade agents and uh memory uh  
**[04:37]** systems uh today so everything inside  
**[04:40]** the last uh end token uh maybe there is  
**[04:43]** a rolling buffer maybe a chat history  
**[04:45]** that gets summarized but when the buffer  
**[04:47]** rolls over your preferences uh actually  
**[04:50]** uh and your past issues and the agent's  
**[04:52]** own decision actually starts vanishing.  
**[04:55]** So that is great for latency and but  
**[04:59]** it's terrible for relationships and we  
**[05:02]** have the uh the final result or the  
**[05:04]** outcome as like a no persistent memory  
**[05:07]** uh at the end. So and and and that's  
**[05:11]** when uh we actually uh started thinking  
**[05:14]** about how our human brain um actually  
**[05:18]** stores these kind of uh information as  
**[05:21]** memory and how we can try to inspire uh  
**[05:23]** that uh uh way of storing u me uh  
**[05:27]** information from our brain and create uh  
**[05:30]** a system or a knowledge graph out of  
**[05:32]** that. So we uh humans uh don't store  
**[05:35]** like a a large uh data chunks or  
**[05:38]** transcript. We remember uh uh  
**[05:41]** information and connections between the  
**[05:43]** information like who did what and like  
**[05:45]** how it was done and and how it uh is uh  
**[05:48]** going on and where uh it is being done.  
**[05:51]** So we remember patterns like this. So  
**[05:54]** let's say like every time this happens  
**[05:56]** uh this is the outcome. So every time I  
**[05:58]** buy a chocolate uh to my brother and he  
**[06:00]** gets uh happy. So that's the kind of uh  
**[06:03]** the relations that our brain actually  
**[06:05]** tries to store and and and that's is  
**[06:08]** actually a graph shaped uh way of  
**[06:10]** storing uh information. So that's the  
**[06:12]** natural way our brain stores and uh many  
**[06:15]** Asians in in in contrast they just uh  
**[06:18]** have a linear text logs and uh large uh  
**[06:21]** text information without actual meaning  
**[06:24]** and uh relations on between the context  
**[06:27]** uh of the information. So Neoforj's view  
**[06:30]** is simple. Uh if your memory is about  
**[06:33]** connections, your memory store should be  
**[06:35]** a graph. So that's the mantra that uh  
**[06:38]** Neo 4G actually tells us. Um so what uh  
**[06:41]** memory really means for these agents. So  
**[06:44]** we can see uh there are five uh  
**[06:46]** different factors here. U let's say the  
**[06:50]** uh recall uh capacity of the agent. So  
**[06:53]** it basically starts to retrieve relevant  
**[06:55]** past information and uh it will try to  
**[06:58]** uh recall the actual uh things that was  
**[07:01]** logged or uh it was uh it dealt before  
**[07:05]** and continuity. So instead of um just  
**[07:08]** like uh having or asking the same  
**[07:10]** question or asking uh new questions or  
**[07:13]** uh starting from scratch uh it will try  
**[07:16]** to sort of maintain that continuity over  
**[07:19]** the sessions and over the days and over  
**[07:21]** the uh timeline and uh the reflections.  
**[07:26]** So it basically tries to learn from the  
**[07:29]** outcomes like sort of kind of an  
**[07:31]** experience like how we humans get  
**[07:32]** experience from our uh day-to-day  
**[07:35]** activities and and and uh scenarios. In  
**[07:38]** a similar fashion uh it tries to reflect  
**[07:41]** and learn from its uh outcomes. So this  
**[07:45]** uh and then finally we have the  
**[07:46]** commitments and identity. Um so it tries  
**[07:49]** to track what are all the goals and what  
**[07:51]** are all the promises and and the task  
**[07:53]** that the user had uh instructed uh it to  
**[07:56]** do and what is the identity that um the  
**[07:59]** user uh basically wants it to do.  
**[08:03]** So then we uh can so now we are moving  
**[08:08]** on to the traditional memory patterns  
**[08:11]** and we can see that um whenever uh  
**[08:15]** basically we have this um data stored in  
**[08:19]** the form of a vectors uh but it actually  
**[08:22]** doesn't uh capture who uh promised what  
**[08:25]** or what uh is the actual uh relationship  
**[08:27]** and meaning uh in that vector database  
**[08:30]** and how it is actually connected um and  
**[08:33]** and and that's when we we we think about  
**[08:36]** uh a graph database like uh a knowledge  
**[08:39]** based graph database uh like Neo 4G and  
**[08:42]** then we have this uh Neo 4G agent memory  
**[08:45]** and memory provides um projects are  
**[08:48]** built on top of idea that we don't just  
**[08:52]** want more text we want a structured  
**[08:55]** evolving memory graph so that's uh where  
**[08:59]** the concept of relationship between the  
**[09:02]** entities also comes come in place and  
**[09:03]** and uh which are actually really  
**[09:06]** essential uh in in uh terms of uh  
**[09:09]** knowledge graphs. So uh these are some  
**[09:12]** of the limitations uh that we had  
**[09:15]** discussed for the traditional memory and  
**[09:17]** moving forward we'll see why do we  
**[09:20]** actually need a knowledge graph and and  
**[09:23]** and how it actually changes the game. So  
**[09:26]** we can see that uh a graph native uh  
**[09:30]** memory layer um basically there are  
**[09:32]** three things in that. So first is we  
**[09:35]** store the entities and relationships. Um  
**[09:38]** then uh second we have the model time uh  
**[09:42]** this um uh so basically this happened in  
**[09:46]** session one then we followed up then the  
**[09:49]** sentiment changed. So that's how it is  
**[09:51]** and and and third we do have multihop  
**[09:53]** recalls. So uh let's say show me the  
**[09:56]** customers whose renewals are nearby uh  
**[09:59]** who's had escalations uh positive and  
**[10:01]** negative sentiments last month. So such  
**[10:04]** kind of uh questions and scenarios we  
**[10:06]** can able to uh uh do with the help of  
**[10:08]** this multihop recall and that's uh  
**[10:12]** exactly what uh Neo4G agent library uh  
**[10:15]** actually does and um as I already  
**[10:18]** mentioned the relationships uh are  
**[10:21]** essential in this and it becomes the  
**[10:23]** first and foremost priority uh when we  
**[10:26]** uh uh discuss about the knowledge graph  
**[10:28]** and create one. So uh if the memory is  
**[10:32]** about connections then then the graph is  
**[10:35]** not an add-on it's a native shape. So as  
**[10:38]** I already mentioned that we inspire um  
**[10:41]** the graph kind of structure from uh the  
**[10:44]** human brain uh how we store and process  
**[10:47]** this information. So that's the basic  
**[10:49]** thing. So if your memor is about  
**[10:51]** connections then you can just close your  
**[10:53]** eyes and go ahead and uh go for the  
**[10:56]** graph uh database.  
**[10:59]** Um so considering our uh example that we  
**[11:02]** had for Johnson who was actually a  
**[11:05]** support specialist and he he wants to  
**[11:07]** solve uh the tickets. So in in in that  
**[11:11]** context uh we can try to think about  
**[11:15]** nodes like uh the user uh the  
**[11:18]** conversation the messages the  
**[11:20]** preferences and uh what are the goals  
**[11:23]** and tickets uh data what are the events  
**[11:26]** data and the decisions and and and the  
**[11:28]** tool calls that is involved uh in the  
**[11:31]** nodes and for uh so once we have the  
**[11:35]** nodes created uh you know and then for  
**[11:38]** these nodes we can create uh the  
**[11:40]** relationships like uh the has preference  
**[11:42]** or the mentioned uh n or the race ticket  
**[11:45]** and who resolved it or what is the  
**[11:47]** promise and led to. So when we have this  
**[11:50]** kind of uh uh nodes and relationship  
**[11:53]** kind of uh and uh entities and  
**[11:57]** relationship kind of graph database it  
**[11:59]** becomes easier for the agent to  
**[12:02]** understand the context. So the agent not  
**[12:05]** only just try to uh bluff the uh text or  
**[12:09]** uh just try to uh uh rewrite or  
**[12:12]** summarize the text. It just understands  
**[12:15]** the actual context understands the  
**[12:18]** meanings and the relationship between  
**[12:20]** these uh notes and then it will try to  
**[12:23]** analyze and then provide the response  
**[12:25]** out of that. So that will make the real  
**[12:27]** difference as compared to the  
**[12:29]** traditional uh systems than the graph  
**[12:31]** systems.  
**[12:33]** and how the uh agents actually basically  
**[12:36]** think. So uh let me just give an  
**[12:40]** complete picture of how what exactly  
**[12:41]** happens um in the back end uh in in the  
**[12:44]** Neo 4G back end. So the user basically  
**[12:46]** sends a message and the Neo4G memory uh  
**[12:50]** the client actually fetches the relevant  
**[12:52]** short-term messages the long-term  
**[12:54]** entities and the reasoning traces that  
**[12:57]** context graph is turned into a prompt  
**[13:00]** for LLM as I mentioned before. So then  
**[13:04]** the agent will try to uh query and uh  
**[13:07]** get the response from the LLM and then  
**[13:09]** it will reply the user for whatever  
**[13:12]** question he has asked. So then uh  
**[13:14]** crucially the memory uh if if it is  
**[13:17]** required then we can actually uh write  
**[13:19]** the back write the new entries or the  
**[13:22]** updated preferences and new decisions  
**[13:24]** back into the uh knowledge uh graph. So  
**[13:29]** uh in a nutshell this is what happens uh  
**[13:32]** when we try to sort of uh create the  
**[13:34]** knowledge graph and query the knowledge  
**[13:36]** graph and and finally uh have that uh  
**[13:40]** information or the new entry stored back  
**[13:42]** in the knowledge graph. uh whenever we  
**[13:45]** try to create such uh systems  
**[13:48]** and these are some of the uh failure  
**[13:51]** stories uh that I was mentioning and uh  
**[13:55]** while in the agenda. So there are some  
**[13:58]** stories that I remember like the  
**[14:00]** groundhog day onboarding flow where uh  
**[14:03]** an assistant asks the same question  
**[14:05]** every Monday and and the end users get  
**[14:08]** annoyed uh with this kind of thing and  
**[14:10]** and it it leads uh to loss of the  
**[14:14]** clients and customers. So and and and  
**[14:17]** then again we have the lost escalation a  
**[14:19]** problem where uh the yesterday's  
**[14:21]** critical incident never shows up in  
**[14:22]** today's conversation and that will lead  
**[14:25]** to uh uh discontinuity or uh we would  
**[14:30]** the person who actually tries to solve  
**[14:32]** that uh uh the tickets or the problem  
**[14:35]** will try to miss that point uh in  
**[14:37]** today's uh conversation uh whenever he's  
**[14:41]** having it with the end user.  
**[14:44]** And then we have the uh stale uh  
**[14:46]** assumption. So where uh the agent still  
**[14:48]** optimizes for uh old long goals after  
**[14:52]** the customer changes the direction. So  
**[14:54]** like none of these are actually uh  
**[14:56]** failures uh when we uh are the actual  
**[14:59]** failures but it's just that these are  
**[15:01]** like having a poor memory uh kind of  
**[15:04]** thing. So the models have a good IQ,  
**[15:08]** they're good at rewriting, they're good  
**[15:09]** at summarizing, everything is super uh  
**[15:11]** and top-notch. But it's the problem  
**[15:14]** about the memory architecture and and  
**[15:16]** that's exactly what uh the Neo4j's uh AI  
**[15:20]** in production examples and the agent  
**[15:22]** memory tools are actually tracking us.  
**[15:25]** And uh one of the other recent uh use  
**[15:28]** case that um I was trying to uh uh work  
**[15:31]** upon is on the financial uh data set  
**[15:34]** that we had for uh the different  
**[15:36]** transaction uh that we do on a monthly  
**[15:38]** basis. So each time uh we always have  
**[15:40]** this question that uh where does my  
**[15:43]** money go and and how do I track it and  
**[15:45]** what uh is my new uh strategy that I can  
**[15:50]** follow to basically save up some money  
**[15:52]** or uh see uh where did uh the actual  
**[15:55]** spend uh that I did on. So in that kind  
**[15:58]** of scenarios also graph uh can play uh a  
**[16:02]** vital role. it can be a best um use case  
**[16:05]** to try on if uh we can uh try to use the  
**[16:09]** graph database to solve these kind of  
**[16:11]** financial analysis problems as well. Um  
**[16:15]** so in today's uh current scenario um so  
**[16:18]** this is what um the a the enterprise AI  
**[16:22]** teams are basically trying to focus on.  
**[16:24]** So they try to uh see uh uh we we have  
**[16:28]** seen lot of uh uh news and uh updates  
**[16:32]** that is coming on about agents about uh  
**[16:35]** uh the systems the workflows the AI  
**[16:39]** automations etc and now uh the teams the  
**[16:42]** enterprises have also started looking  
**[16:44]** about the context graphs the knowledge  
**[16:46]** graphs so they're trying to see and  
**[16:48]** adopt uh these graphs into their uh  
**[16:51]** workflows uh especially when uh a  
**[16:54]** complex and deep understanding is  
**[16:55]** required in in uh the use case. Right?  
**[17:00]** So the uh enterprises have started uh  
**[17:03]** shifting uh towards uh the uh shifting  
**[17:07]** to uh their lens towards these context  
**[17:09]** graphs and started uh actually focusing  
**[17:12]** more towards that and implementing that  
**[17:14]** in their uh uh use cases. So I think u  
**[17:19]** uh that's uh most about uh what we have  
**[17:23]** discussed on um the knowledge graphs and  
**[17:26]** we can also see uh the different  
**[17:27]** benefits of actually using uh or  
**[17:30]** creating this persistent evolving and  
**[17:32]** reliable systems. So uh the basically  
**[17:36]** lot of benefits uh we have discussed  
**[17:38]** upon but uh these are some of the  
**[17:40]** important uh factors and benefits uh out  
**[17:43]** there. So uh we can always try to or or  
**[17:46]** we can also say this is kind of a best  
**[17:48]** practice or handbook uh kind of a thing  
**[17:51]** when we whenever we are trying to uh  
**[17:53]** create the knowledge graph. So uh  
**[17:55]** whenever we are trying to uh create a  
**[17:58]** knowledge graph we can uh we always want  
**[18:00]** to have a separate logs uh from the  
**[18:03]** curated memory graph and and we also  
**[18:05]** want to uh track the time uh the source  
**[18:08]** and the confidence of the uh entities  
**[18:11]** and responses and uh we can store the  
**[18:14]** facts preferences and uh events u u  
**[18:18]** basically whenever we are trying to uh  
**[18:20]** set up these uh nodes and uh  
**[18:22]** relationships  
**[18:24]** Uh and then uh we also uh let the agent  
**[18:27]** uh reflect and update the beliefs on it.  
**[18:30]** Uh let the agent continuously learn from  
**[18:32]** whatever it has produced. Uh and try to  
**[18:36]** uh come up with the better and most  
**[18:38]** relevant and meaningful responses each  
**[18:40]** time uh whenever the user queries on  
**[18:44]** this kind of a knowledge graphs. And  
**[18:46]** then uh we finally have uh the design  
**[18:49]** for correcting and forgetting. Instead  
**[18:52]** of your agent being uh amnesic uh you  
**[18:55]** can uh try to implement these kind of uh  
**[18:58]** knowledge graphs to be more uh reliable  
**[19:01]** and persistent systems and so that it  
**[19:04]** doesn't actually uh starts uh forgetting  
**[19:06]** things but it actually learns and uh  
**[19:10]** understands your use case better your  
**[19:12]** tasks and works better and then uh  
**[19:14]** support and provide you uh the best uh  
**[19:17]** uh outcome and results uh going forward.  
**[19:21]** So we have almost reached uh to the end  
**[19:24]** of uh our slide. Uh I'll leave you with  
**[19:26]** uh this uh questions and these thoughts  
**[19:30]** to ponder upon. So if uh AI can't  
**[19:33]** remember the relationships, can it  
**[19:35]** really be your assistant? Can it really  
**[19:37]** be your super intern that we call? And  
**[19:41]** uh we have spent years pushing for uh  
**[19:43]** big context windows and uh bigger models  
**[19:46]** and we still uh try to thrive upon uh  
**[19:49]** creating uh more robust and bigger  
**[19:51]** models. But uh what uh builds trust,  
**[19:55]** right? And uh would you trust an AIS  
**[19:58]** system that actually forgets uh things  
**[20:00]** and and and should memory be the uh new  
**[20:03]** frontier um in in in the coming uh  
**[20:07]** future? So that's uh what I would like  
**[20:11]** to uh leave upon uh for you guys and um  
**[20:16]** yeah so that's uh it from my side. Uh  
**[20:20]** thanks for attending. We can stay  
**[20:21]** connected um in the LinkedIn. Yeah.  