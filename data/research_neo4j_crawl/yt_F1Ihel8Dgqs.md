# Transcript: https://www.youtube.com/watch?v=F1Ihel8Dgqs

**Language:** English (auto-generated) (en) — auto-generated
**Snippets:** 619

---

**[00:08]** Great. Thanks a lot. Hey everyone,  
**[00:10]** thanks for joining today. Hope uh Nodes  
**[00:13]** AI has been been a good event for folks  
**[00:16]** uh so far that are watching live. And if  
**[00:19]** you're catching the recording uh welcome  
**[00:21]** to you as well. You can find my slides  
**[00:25]** uh either by scanning that QR code or  
**[00:28]** the the URL down in the bottom left  
**[00:31]** graph.com/nodesai2026.  
**[00:35]** I'll put that in the chat too and um we  
**[00:37]** we'll share that again at the end too.  
**[00:39]** Uh but it might be some useful resources  
**[00:41]** to to check out some of the slides. Um I  
**[00:45]** want to pick up kind of right where you  
**[00:48]** know we left off in the um session  
**[00:51]** earlier this morning in the panel  
**[00:54]** discussion in the keynote. I want to  
**[00:56]** pick up some of the the topics there  
**[00:58]** that we touched on and and maybe drill  
**[01:00]** in a little bit um specifically around  
**[01:03]** context graphs, agent memory on  
**[01:06]** ontologies, these sorts of things. So,  
**[01:09]** I'm going to jump uh jump right in. And  
**[01:12]** the first thing I want to talk about and  
**[01:13]** and this came up in the in the panel  
**[01:15]** discussion uh is this relationship  
**[01:18]** between context graphs and agent memory.  
**[01:22]** And so,  
**[01:24]** you know, I said earlier today that  
**[01:26]** there's this this close relationship. I  
**[01:28]** don't think it's quite onetoone but I  
**[01:30]** think there's a very close relationship  
**[01:32]** between context graphs um and and we'll  
**[01:37]** we'll go through a refresher on on  
**[01:39]** context graphs and in a second but  
**[01:41]** there's been a lot of discussion around  
**[01:43]** context graphs today but context graphs  
**[01:46]** and agent memory with with memory we're  
**[01:48]** typically thinking about some text  
**[01:51]** representation some uh expression of a  
**[01:54]** preference or something that happened.  
**[01:58]** Um, but you know this typically like  
**[02:01]** file or vector like textbased um is how  
**[02:06]** uh often times we're initially  
**[02:08]** implementing uh some of these things.  
**[02:11]** But with something like uh like a  
**[02:13]** context graph or graphbased memory,  
**[02:17]** we're actually extracting out the  
**[02:19]** entities. So what are the what are the  
**[02:21]** things mentioned in the conversation and  
**[02:24]** identifying the relationships? uh  
**[02:27]** between them. I think that's one of the  
**[02:28]** the most important uh you know first  
**[02:32]** things that we need to think about when  
**[02:34]** we're working with graphs uh with with  
**[02:36]** agent memories. How do we uh identify  
**[02:38]** the entities? How do we go from  
**[02:40]** unstructured data to identifying like  
**[02:42]** what are the the things like right like  
**[02:44]** the entities are the things that exist  
**[02:46]** events these are things that have  
**[02:48]** happened and then context in in the  
**[02:51]** context graph terminology the the  
**[02:54]** decision traces. This is the the why,  
**[02:57]** right? These are the policies that were  
**[02:58]** applied, the risk factors, the reasoning  
**[03:01]** that was applied either by um a human  
**[03:04]** employee or or by an agent applying some  
**[03:06]** policy. But we need some uh some insight  
**[03:09]** into the decision that was applied. And  
**[03:15]** um I wrote a blog post a few months ago  
**[03:17]** and and showed this this demo  
**[03:19]** application. that's probably um still up  
**[03:21]** and running, but basically a context  
**[03:23]** graph for a financial services  
**[03:25]** organization. Um you know, we can do  
**[03:28]** things like ask for uh credit approval  
**[03:32]** decisions or responding to customer  
**[03:36]** support questions as they uh as they  
**[03:38]** come in. And really the the architecture  
**[03:42]** for this is we give the agent tools. So  
**[03:45]** we give them some uh functionality, some  
**[03:47]** way to interact with and understand  
**[03:49]** their environment by querying, updating  
**[03:53]** the context graph uh and finding the  
**[03:57]** most relevant decisions uh applying  
**[04:00]** those policies, generating a  
**[04:01]** recommendation is a core part of what  
**[04:03]** that agent um is doing. Graph data  
**[04:06]** science is an important component of  
**[04:08]** this. Uh we can use the structure of the  
**[04:11]** graph through uh through node  
**[04:12]** embeddings. We can use things like  
**[04:15]** community detection to help us find and  
**[04:18]** and service the most recent or the most  
**[04:20]** relevant uh context and and decision for  
**[04:23]** any step uh that we are in uh in sort of  
**[04:27]** our uh agent interaction.  
**[04:31]** And this is largely based on the Neoraj  
**[04:35]** agent memory Python package which  
**[04:38]** exposes short-term long-term and  
**[04:40]** reasoning memory. So there's an  
**[04:42]** important observation that context  
**[04:44]** graphs need three types of memory. Um  
**[04:47]** when we're talking about agent memory um  
**[04:49]** often times we're thinking about  
**[04:52]** preferences or u we're thinking about  
**[04:55]** conversations but reasoning the decision  
**[04:57]** traces these are also an important part  
**[04:59]** of agent memory. Sometimes this is  
**[05:01]** called procedural memory or experiential  
**[05:04]** memory uh things like that. But these  
**[05:06]** are all abstractions that are baked into  
**[05:08]** the Neo Forj agent memory package um  
**[05:10]** which we can install uh through pip and  
**[05:15]** integrates with pretty much any  
**[05:18]** Pythonbased uh agent framework uh and  
**[05:22]** has lots of configurable functionality  
**[05:24]** for things like entity extraction and  
**[05:26]** working with graph data science. Now I  
**[05:29]** mentioned these these three types of  
**[05:30]** agent memory short-term long-term and  
**[05:34]** reasoning memory. Uh short-term memory  
**[05:36]** we can think of as conversations, right?  
**[05:39]** Conversation history, session state. Uh  
**[05:42]** this is really though an entry point  
**[05:45]** into entity extraction, right? So uh  
**[05:48]** we're talking about conversational so  
**[05:50]** unstructured data uh conversations with  
**[05:53]** an agent. And in that uh in that text  
**[05:59]** unstructured data, we're going to be  
**[06:00]** mentioning things, right? we're going to  
**[06:02]** be mentioning customers or uh products,  
**[06:05]** accounts, we need to go through this  
**[06:07]** entity extraction and entity resolution  
**[06:09]** phase to understand what what is the  
**[06:11]** actual thing that uh that we're talking  
**[06:13]** about and applying just an LLM only  
**[06:17]** approach to entity extraction and entity  
**[06:20]** resolution can be quite uh slow and and  
**[06:23]** quite expensive. And so as part of the  
**[06:26]** Nej agent memory package, we've built  
**[06:28]** this uh multi-stage sort of entity  
**[06:31]** extraction pipeline that is able to use  
**[06:35]** uh named entity resolution like like  
**[06:37]** statistical NLP methods as well as  
**[06:40]** smaller local models like the the gler  
**[06:42]** fine-tune models for entity extraction  
**[06:44]** that can run on CPU um to run locally  
**[06:47]** for free essentially with fallback to  
**[06:49]** LLM for more complex uh extraction and  
**[06:54]** resolution.  
**[06:55]** Now, the data model that we apply during  
**[06:58]** entity extraction and resolution is  
**[07:01]** really important. And that data model, I  
**[07:03]** think, is going to depend on the domain  
**[07:07]** uh that we're working with. Right now,  
**[07:09]** by default, Nefj agent memory uses the  
**[07:13]** pole plus O entity model. This is a a  
**[07:16]** common model that's used in  
**[07:18]** investigations, right? So, person,  
**[07:20]** organization, location, event, object.  
**[07:24]** Um, this this I think of as kind of the  
**[07:27]** the starting point. Um, but as you're  
**[07:30]** going through and  
**[07:32]** implementing your own agent memory, I  
**[07:34]** would really encourage you to extend the  
**[07:36]** the base data model, the base ontology,  
**[07:39]** uh, that's used, and we'll see how to do  
**[07:41]** that, uh, in a moment here. reasoning  
**[07:43]** memory. This is the the third type of  
**[07:46]** memory uh that we mentioned that's  
**[07:48]** supported by the Nej agent memory  
**[07:50]** package. And this is really all about  
**[07:52]** understanding that why, right? The the  
**[07:55]** missing piece, the explanation of uh  
**[07:59]** what execution plan did the agent make?  
**[08:02]** Why was the decision made? What are the  
**[08:04]** decision traces? What are the uh what  
**[08:06]** can we observe from uh the agent's  
**[08:09]** reasoning phase? Those sorts of things  
**[08:11]** are captured in uh reasoning memory and  
**[08:14]** altogether um these are the the main  
**[08:18]** abstractions for working with memory in  
**[08:20]** the nearfj agent memory package  
**[08:22]** altogether short-term memory long-term  
**[08:24]** memory reasoning memory these together  
**[08:26]** make up your context graph and they're  
**[08:29]** they're all related right so so messages  
**[08:32]** uh these can trigger a a reasoning trace  
**[08:37]** they can trigger like the reasoning  
**[08:38]** phase for the agent. Um, we extract  
**[08:43]** specific entities from specific  
**[08:45]** messages. Messages trigger a tool called  
**[08:48]** the these sorts of things.  
**[08:51]** We've been working a lot with the  
**[08:54]** different framework uh and agent uh  
**[08:57]** cloud orchestration vendors. Um, and so  
**[09:00]** we we've spent a lot of work making sure  
**[09:02]** that near agent memory integrates well  
**[09:04]** with Google ADK, uh, with AWS, Microsoft  
**[09:08]** Agent Framework. Um, and so you'll see  
**[09:11]** some specific examples and and specific  
**[09:13]** integrations with some of those, uh,  
**[09:16]** those tools as well. But there's still a  
**[09:20]** bit of a a challenge that I saw after we  
**[09:22]** um after we released this and and it was  
**[09:24]** great to see folks adopting um  
**[09:26]** especially some of the more uh  
**[09:28]** sophisticated agent memory integrations  
**[09:31]** um that are out there but I I think  
**[09:33]** there's still a bit of an overhead in  
**[09:35]** surfacing some of this data like how do  
**[09:37]** I actually surface the decisions that  
**[09:40]** have been made in the organization? How  
**[09:41]** do I actually get that data uh into the  
**[09:44]** graph? How do I expose that as a tool  
**[09:47]** for my agent to make sense of? And so to  
**[09:50]** to help smooth that process a bit, we  
**[09:52]** created the create context graph  
**[09:55]** project. Um create context graph. This  
**[09:57]** is inspired by the create react app  
**[09:59]** project which which was for a while kind  
**[10:01]** of the default way of creating a react  
**[10:03]** application. Go through this interactive  
**[10:06]** scaffold and choose uh sort of what what  
**[10:09]** domain are you working with? Do you want  
**[10:11]** to import real data? Do you want sample  
**[10:14]** data? just to get started. Uh that's  
**[10:16]** kind of the the basic idea. Um and let's  
**[10:19]** take a look at at what this looks like.  
**[10:21]** So if I run uvx create context graph, uh  
**[10:25]** it'll take me through this interactive  
**[10:28]** workflow. Let's say uh I'm going to  
**[10:31]** create a science graph project. So we  
**[10:34]** can uh suck in SAS data or generate demo  
**[10:37]** data. Let's do demo data for scientific  
**[10:41]** research.  
**[10:43]** And we can choose which agent framework  
**[10:45]** we want. Uh let's go with cloud code.  
**[10:48]** And I'm going to use an existing Neo  
**[10:51]** forj instance. We can also connect to  
**[10:53]** nearjura instance or uh use docker. But  
**[10:56]** I have an instance running locally  
**[11:00]** on  
**[11:01]** let's see localhost.  
**[11:10]** There we go. And we're going to skip the  
**[11:13]** kind of optional enhancements and and  
**[11:15]** add-ons here. And here I'm being asked  
**[11:18]** to add um an anthropic API key. And and  
**[11:20]** these are optional for my agent. I I can  
**[11:23]** use whatever model um I want. By  
**[11:25]** default, we'll use  
**[11:27]** um anthropic sonnet model and OpenAI  
**[11:31]** embeddings.  
**[11:34]** So we've now uh provisioned out kind of  
**[11:38]** this full stack  
**[11:41]** context graph application. I'm just  
**[11:43]** installing some dependencies. This step  
**[11:45]** here to download um the spacey model.  
**[11:47]** This is probably the uh the longest step  
**[11:50]** of of what we're going to uh see here.  
**[11:53]** But if we go to the uh the docs here,  
**[11:55]** this is the create context graph um page  
**[12:00]** which has um documentation. There's good  
**[12:03]** um tutorials here. We're basically  
**[12:04]** following through this your first uh  
**[12:07]** context graph app. Uh but okay, now  
**[12:10]** we're installing uh the uh front-end  
**[12:13]** dependencies and so the front end is a  
**[12:16]** uh Nex.js application. Um and so we saw  
**[12:20]** earlier we had our choice of backend  
**[12:23]** framework, right? And and so we chose I  
**[12:25]** think the cloud uh cloud agent SDK. We  
**[12:27]** could have chosen any of the the Python  
**[12:29]** models supported by uh supported by  
**[12:35]** uh near agent memory. Okay, cool. And so  
**[12:37]** then the next step is to uh seed our  
**[12:42]** database. So we'll run the  
**[12:46]** make seed and this is going to just load  
**[12:49]** some sample data uh in my database. And  
**[12:52]** then finally  
**[12:54]** we can run make start and this is going  
**[12:56]** to run uh the back end and the front-end  
**[12:59]** application. So now if we go to  
**[13:04]** localhost 3000  
**[13:09]** and zoom in a bit we should see this is  
**[13:12]** our full stack uh scientific research  
**[13:17]** context graph. So the first thing we see  
**[13:18]** is the data model. Um but we can ask  
**[13:23]** some uh questions here something like um  
**[13:27]** show me the citation network around deep  
**[13:30]** learning in drug discovery. And we can  
**[13:34]** see what our uh our agent has access to  
**[13:37]** a number of tools and it's going to  
**[13:40]** choose which tools to execute uh to try  
**[13:43]** to answer uh this question right. uh and  
**[13:46]** initially it's found um a paper here. We  
**[13:49]** can explore uh the paper and the uh the  
**[13:53]** citation network around that to bring in  
**[13:57]** uh more data and that's essentially what  
**[13:58]** our our agent is doing here. Um sort of  
**[14:01]** doing text decipher to bring in more  
**[14:04]** data to answer um our question.  
**[14:09]** Now what data did we actually bring in  
**[14:12]** like this? This is sample data. We we we  
**[14:15]** see like documents. I have kind of  
**[14:17]** decision traces here. Um I have like  
**[14:22]** like science papers. I have like  
**[14:25]** researchers that are affiliated. And you  
**[14:26]** can see like this this data matches uh  
**[14:29]** the domain that I chose and was all  
**[14:31]** generated uh by piping  
**[14:36]** work documentation. Right? So, uh, in in  
**[14:39]** this case, we're working with science  
**[14:41]** papers, meeting notes, uh, from, uh,  
**[14:45]** organizations that are allocating, uh,  
**[14:49]** grants, the these sorts of things.  
**[14:51]** We're, uh, taking documents that  
**[14:53]** represent that sort of work product and  
**[14:55]** running that through the NEFJ agent  
**[14:57]** memory entity extraction pipeline to  
**[15:00]** construct uh, this context graph.  
**[15:04]** So that is one way to get started uh  
**[15:07]** with context graphs and the  
**[15:11]** Nej agent memory um package that that's  
**[15:15]** using sample data right and and that  
**[15:17]** that's helpful for for demos but h how  
**[15:19]** do we surface like the these realw world  
**[15:22]** decisions that occurred um and for that  
**[15:26]** we can use the uh SAS connector data in  
**[15:31]** the create context graph project  
**[15:33]** currently there support for um GitHub  
**[15:36]** linear, Google workspace,  
**[15:38]** uh cloud code, there may be a few others  
**[15:41]** um that we've added in there, but the  
**[15:43]** basic idea is we can um include a  
**[15:47]** connector um or you saw when we're going  
**[15:50]** through the interactive flow uh we were  
**[15:53]** being um asked if we wanted demo data or  
**[15:56]** uh to connect to SAS to to a SAS service  
**[15:59]** to pull in um real data. And so for  
**[16:04]** cloud code for example um the connector  
**[16:06]** works by parsing  
**[16:09]** uh the JSONL session files that we have  
**[16:13]** uh locally on our machine uh and we'll  
**[16:16]** parse those into a context graph and  
**[16:20]** look at like what are the uh what are  
**[16:24]** what is the like graph structure of our  
**[16:28]** sessions that we've had with cloud code.  
**[16:30]** Right? So cloud code is a a coding  
**[16:32]** agent. I interact with it by you know  
**[16:36]** sort of sending messages that can either  
**[16:38]** be um you know feedback on a plan or uh  
**[16:45]** maybe a PRD but it it's somehow related  
**[16:48]** to some project that I'm working on. I'm  
**[16:50]** going to be calling tools uh to update a  
**[16:53]** file. Right. Right. Like the these sorts  
**[16:55]** of of interactions.  
**[16:57]** Now, an important component though of of  
**[16:59]** context graphs is surfacing the decision  
**[17:03]** trace, right? Like what were the  
**[17:05]** decisions that were made either by a  
**[17:07]** human or or by an agent and  
**[17:09]** materializing those surfacing those from  
**[17:12]** uh from our work product. And here's an  
**[17:14]** example in the cloud code connector for  
**[17:18]** create context graph. We do this using  
**[17:20]** some heruristics. Um and so essentially  
**[17:23]** we're looking for the case where there  
**[17:25]** was some user correction um or maybe  
**[17:29]** user chose to change dependency uh or  
**[17:32]** there was some error. How did we resolve  
**[17:34]** the error? Um we were presented with an  
**[17:36]** alternative uh that was like a clear  
**[17:39]** decision that the the human had to make  
**[17:41]** based on you know maybe an architecture  
**[17:42]** decision these sorts of things. Now  
**[17:45]** what's really important is when we're  
**[17:46]** able to combine these data sources and  
**[17:49]** query across them. So here we're adding  
**[17:52]** the Google Workspace and the linear uh  
**[17:56]** connector. And so we can combine  
**[17:59]** projects that we found in cloud code  
**[18:03]** with uh linear work items and maybe PRDS  
**[18:07]** that we found in Google Workspace for  
**[18:10]** example.  
**[18:13]** So here's just another look at some of  
**[18:15]** the heristics we use for the um the  
**[18:19]** decision extraction  
**[18:21]** um and some examples right where I'm I'm  
**[18:25]** using explicit statements right always  
**[18:27]** use uh single quotes for example right  
**[18:30]** they're those are easy to um to sort of  
**[18:32]** have reg x reg x's that are trying to  
**[18:35]** identify um those sorts of explicit  
**[18:38]** statements behavioral patterns are uh  
**[18:40]** are more interesting and and tricky to  
**[18:42]** identify.  
**[18:46]** Cool. So, this is my second demo that I  
**[18:50]** wanted to show. Um, but maybe I'll I'll  
**[18:53]** skip sort of this process since we're um  
**[18:56]** have limited time here. Uh, we'll skip  
**[18:59]** the import process, but I'll show you a  
**[19:01]** bit of what this looks like. Uh, so I  
**[19:03]** pointed this at my uh Aura instance.  
**[19:08]** Zoom in a little bit here.  
**[19:12]** And we can see here uh if we start by  
**[19:15]** querying uh for projects. See I have 16  
**[19:20]** projects. Um this is  
**[19:24]** grouse flocks. Oh, this was a uh this  
**[19:27]** was an experiment on um adding some new  
**[19:31]** visualization styling um using the uh  
**[19:34]** the NVL  
**[19:36]** um  
**[19:38]** uh the NVL visualization uh package. And  
**[19:41]** so anyway, we can see the the message  
**[19:43]** the messages that were sent the the tool  
**[19:45]** calls that were made. Here's a tool name  
**[19:47]** uh edit, which is essentially, you know,  
**[19:50]** editing um a file. always see the file  
**[19:51]** that was updated and and um so on. Uh  
**[19:55]** and we have the same full stack like  
**[19:57]** like front end piece that we can use to  
**[19:59]** interact with that uh as well as part of  
**[20:02]** create context graph.  
**[20:06]** Cool. So the third piece that I want to  
**[20:09]** talk about here is this idea of multi-  
**[20:13]** aent memory. So  
**[20:16]** I I I think it's you know somewhat  
**[20:18]** intuitive when we're interacting with a  
**[20:20]** single maybe maybe a a coding agent  
**[20:22]** using the cloud code example. Um these  
**[20:25]** are the preferences that I personally  
**[20:27]** care about and and we can extract that  
**[20:29]** and and maybe a markdown file for saving  
**[20:32]** that you know locally is is fine. But  
**[20:36]** the case where we have you know hundreds  
**[20:38]** or thousands of agents that are  
**[20:41]** collaboratively working together uh how  
**[20:44]** can we enable memory uh and specifically  
**[20:48]** the context graph the um that we're  
**[20:50]** using with new agent memory how can that  
**[20:52]** be a shared coordination layer uh for  
**[20:56]** our like swarm of agents essentially  
**[20:59]** right like databases were created to  
**[21:01]** solve this coordination problem there  
**[21:03]** there a lot of advantages that we can  
**[21:04]** have there as we're leveraging that um  
**[21:07]** that graph database as our context graph  
**[21:11]** memory layer. Um let's look at another  
**[21:13]** example. Um so here we have uh kind of  
**[21:17]** an agent swarm again in the financial  
**[21:19]** services domain. Uh we have in this case  
**[21:24]** a series of agents that uh are all  
**[21:27]** implemented in the same agent framework.  
**[21:28]** So they're all implemented in AWS  
**[21:30]** strands. They share a  
**[21:33]** uh memory layer, but they all have a  
**[21:35]** somewhat different persona, right? So,  
**[21:37]** we have a know your customer agent, an  
**[21:40]** anti-moneyaundering agent, a compliance  
**[21:42]** agent. They all have somewhat different  
**[21:45]** uh personas, somewhat different  
**[21:46]** outcomes, somewhat different goals, but  
**[21:49]** they have that shared memory layer still  
**[21:52]** um because they're all using agent  
**[21:55]** memory. they all have this the same  
**[21:56]** conventions, the same data models that  
**[21:58]** they're using, the same contract  
**[22:00]** essentially um with the database for the  
**[22:04]** shape of their memory. And so uh a  
**[22:06]** typical workflow might be something like  
**[22:08]** this where uh the know your customer  
**[22:10]** agent is you know ingesting new customer  
**[22:13]** data going through this entity  
**[22:14]** extraction. Maybe it has some uh process  
**[22:18]** for flagging uh suspicious transactions.  
**[22:21]** Uh and this can happen just in the  
**[22:23]** memory layer. So in in the the memory  
**[22:26]** layer the the KYC agent you know maybe  
**[22:29]** flags that oh this is a suspicious  
**[22:32]** relationship that's immediately  
**[22:33]** available for say the credit agent to  
**[22:36]** pick up on because that is in the uh  
**[22:39]** shared memory layer. Now this example I  
**[22:42]** think this this makes sense to us and  
**[22:44]** and we said okay these are all written  
**[22:46]** using the same uh agent framework the  
**[22:49]** same like newj agent memory uh  
**[22:52]** integration for strands is kind of how  
**[22:54]** these were implemented but what if we  
**[22:56]** had you know a system where we had many  
**[22:59]** different agents implemented in many  
**[23:01]** different languages or uh you know  
**[23:03]** different frameworks we have different  
**[23:06]** um you know different teams throughout  
**[23:08]** our organization that are all working on  
**[23:11]** um you know different pieces of  
**[23:12]** technology. Having a shared memory layer  
**[23:16]** uh that all of our agents conform to the  
**[23:20]** same conventions uh means that our  
**[23:23]** memory layer can then be the layer of  
**[23:26]** coordination for our agents. But we need  
**[23:28]** some way to certify that uh those agents  
**[23:33]** are all using uh the same conventions  
**[23:35]** that the memory layer that they're using  
**[23:38]** is compatible. Uh, and this is where uh  
**[23:41]** technology compliance kit testing comes  
**[23:44]** in. Um, and so this I think is something  
**[23:47]** we're going to be uh working on in our  
**[23:49]** our agent memory tooling quite a bit  
**[23:52]** going forward is being able to certify  
**[23:54]** uh that different agent memory  
**[23:56]** implementations adhere to the same  
**[23:58]** conventions. They have the same shape  
**[24:00]** and behavior of agent memory uh in the  
**[24:04]** graph. And when when we do that, we're  
**[24:06]** able to share uh this agent memory layer  
**[24:09]** as a coordination layer. Um and so we've  
**[24:13]** begun some initial work there. There's a  
**[24:14]** link here to the agent memory uh TCK  
**[24:18]** repo which has um the specification and  
**[24:22]** and some of the um conventions that  
**[24:26]** we're using in the NearFJ agent memory  
**[24:29]** tooling. This this is by no means uh  
**[24:31]** done and comprehensive. just sort of a  
**[24:34]** first stab I think at what this looks  
**[24:37]** like. Um, and there's an example  
**[24:39]** application in there of uh I think we  
**[24:41]** have six agents written in in different  
**[24:43]** languages from Python, TypeScript, Go, C  
**[24:47]** um multiple versions,  
**[24:50]** multiple um Python frameworks. Um, and  
**[24:53]** then also just earlier today I got the  
**[24:54]** the R uh version working. So if anyone  
**[24:57]** is is interested in um Rlang and and  
**[25:01]** agent memory for R, we can now have sort  
**[25:04]** of a agent memory client um in that. So  
**[25:06]** anyway, that I think is just kind of the  
**[25:09]** the vision that I want to set out um for  
**[25:12]** going forward in the future is you  
**[25:15]** imagine we have uh all of these agents  
**[25:18]** in different languages, different  
**[25:20]** frameworks, all uh working together  
**[25:23]** contributing to learning from uh the  
**[25:26]** same shared memory layer. Cool. Well, I  
**[25:30]** think we're we're about out of time. Um,  
**[25:33]** but I'll I want to leave some resources  
**[25:34]** up and then we'll we'll go through some  
**[25:36]** questions uh if we have time for them.  
**[25:38]** Here's some some links to some of the  
**[25:40]** things I talked about. Um, Graph Academy  
**[25:43]** is always a a good place to start.  
**[25:46]** There's a new Graph Academy context  
**[25:48]** graph course. Um, take a look at that.  
**[25:50]** the create context graph project. That  
**[25:53]** is the command line tool used to  
**[25:55]** scaffold up your your context graph  
**[25:57]** application which is built on top of the  
**[26:00]** Neoraj agent memory uh package. So those  
**[26:03]** are some resources um I would encourage  
**[26:06]** folks to check out. Um I want to leave  
**[26:08]** you with I think what was my favorite  
**[26:11]** paper uh from last year. This came out  
**[26:14]** just the end of last year and this was  
**[26:16]** kind of a survey of memory in the age of  
**[26:20]** AI agents. And I think it does a really  
**[26:22]** good job of presenting a few different  
**[26:25]** ways to to slice up the memory landscape  
**[26:28]** based on sort of like the the form  
**[26:31]** function or or dynamics of the memory  
**[26:34]** system. Um and so I'd encourage folks to  
**[26:37]** to check this out. We I talked about  
**[26:39]** some of the the aspects but just maybe  
**[26:41]** not through the same lens. Um, so I I  
**[26:44]** would encourage you to check this paper  
**[26:46]** out um as a good way to uh to sort of  
**[26:49]** have a different lens on uh the memory  
**[26:52]** landscape piece. And I see a few folks  
**[26:55]** asking for the slides. Yes, the slides.  
**[26:57]** I usually have a link at the end. I  
**[26:58]** forgot that. But if we zoom all the way  
**[27:01]** to the beginning, uh we have yes, the  
**[27:04]** slides here. So the link is  
**[27:06]** graph.com/nodesai  
**[27:11]** 2026.  
**[27:12]** I can write that in graph  
**[27:15]** stuff.com. Nodes AAI.  
**[27:19]** There we go. I think I typed that right.  
**[27:20]** We'll see. Cool. So we have just a a few  
**[27:25]** minutes left. Um not sure if we have  
**[27:28]** time to take questions here.  
**[27:32]** Let's see. I'll just scroll through the  
**[27:34]** chat. Maybe take one or two.  
**[27:40]** Uh let's see.  
**[27:44]** So I see a few a few folks asking about  
**[27:48]** the um like the difference between the  
**[27:51]** industry domains in in create context  
**[27:54]** graph and like the the connector data.  
**[27:57]** So yeah, maybe that's a that's good um a  
**[28:00]** good shout there. So the idea with  
**[28:03]** create context graph is really to be  
**[28:07]** able to get started with this this full  
**[28:09]** text graph uh application. Um and so  
**[28:14]** really the idea is  
**[28:16]** choosing a domain and an agent  
**[28:19]** framework. Um and then if you want to  
**[28:23]** work with sample data or if you want to  
**[28:25]** actually connect your own um SAS service  
**[28:29]** like linear GitHub uh and uh if you do  
**[28:33]** that we'll actually try to identify uh  
**[28:37]** some of the decisions that were made in  
**[28:40]** your in your work documents um through  
**[28:42]** that that process that I talked about.  
**[28:46]** Cool. And so I see we have um  
**[28:50]** one minute left. So maybe we will pause  
**[28:54]** there because I think we're going to  
**[28:55]** head into the next session soon.  