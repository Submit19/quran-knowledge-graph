# Transcript: https://www.youtube.com/watch?v=sZRA4j3d0c8

**Language:** English (auto-generated) (en) — auto-generated
**Snippets:** 785

---

**[00:03]** [music]  
**[00:05]** All right. Hello everyone. My name is  
**[00:07]** Zach. I am a AI and machine learning  
**[00:11]** product specialist here at Neo Forj. And  
**[00:14]** I'd like to take some time to talk to  
**[00:16]** you about building intelligent AI  
**[00:18]** systems and some of the new cool tools  
**[00:20]** that we have coming out to help you do  
**[00:22]** that. Um, so the way that I've organized  
**[00:25]** this is I'm going to talk about some of  
**[00:26]** the new things that are coming out. This  
**[00:28]** is going to be Aura agents and MCP  
**[00:30]** server for Neo forj. So I'll mention  
**[00:32]** those really quickly, but then I  
**[00:34]** actually wanted to get into sort of why  
**[00:36]** graphs for AI in general and sort of how  
**[00:38]** graph and graph rag help with context  
**[00:41]** engineering. Um I'll show you some stuff  
**[00:43]** through our new uh MCP server for Neo  
**[00:46]** Forj. Um, I'll take a deeper walkthrough  
**[00:48]** through Aura Agents, which is a really  
**[00:50]** cool new platform, and then I'll go over  
**[00:53]** some follow-up resources for learning  
**[00:55]** and just getting more hands-on uh with  
**[00:57]** the product and uh different resources  
**[00:59]** we have here at Neo for today. Um, so  
**[01:03]** what's new? So, there's two cool things  
**[01:05]** that recently came out. Um, first I want  
**[01:08]** to talk about the MCP server for Neo  
**[01:11]** Forj. So for those of you that have  
**[01:13]** followed us at Neo Forj for a while, you  
**[01:15]** know that we have model context protocol  
**[01:17]** servers uh that have been available  
**[01:19]** through labs. Um and MCP is just a  
**[01:22]** protocol that exposes uh a bunch of  
**[01:25]** tools, right? It's a standard to  
**[01:26]** different uh agents and AI systems. Um  
**[01:29]** and we can expose Neo forj to that. And  
**[01:31]** recently what we've done is we've taken  
**[01:33]** that into our core engineering and we  
**[01:35]** now have an officially supported MCP  
**[01:37]** server that's in beta. It's available  
**[01:39]** today. Um it's been written in Go. It's  
**[01:42]** open source right now. You can get it  
**[01:43]** and manage it yourself and then connect  
**[01:45]** it uh to your Neo Forj data. Um and then  
**[01:48]** the next thing uh that is also really  
**[01:51]** cool is our Aura agents that is in early  
**[01:54]** access right now. So it's in an early  
**[01:56]** access program or EAP. And what that is  
**[01:59]** is basically an end toend platform that  
**[02:01]** lets you build, test, and deploy agents  
**[02:03]** in a matter of minutes. It's low code,  
**[02:06]** no code. um it is grounded, you know, by  
**[02:09]** default inside of your knowledge graphs,  
**[02:12]** uh basically one of your ORDB instances.  
**[02:14]** Um and it's [clears throat] going to go  
**[02:16]** GA later this year. So, I'll show you  
**[02:19]** both of these things live uh in a demo.  
**[02:21]** But before I do that, I just want to  
**[02:23]** talk about why graphs for AI. Um and  
**[02:26]** basically what graphs help you do is  
**[02:28]** manage context to boost accuracy,  
**[02:30]** improve explanability, and future proof  
**[02:32]** your AI systems. Um, and I have a little  
**[02:35]** diagram here, uh, that I can show you  
**[02:37]** which kind of runs through the general  
**[02:39]** graph architecture that we often see.  
**[02:42]** Um, and a lot of these components will  
**[02:44]** look familiar, right? You'll have a UI  
**[02:46]** that exposes enterprise search or some  
**[02:48]** sort of knowledge assistant. You'll have  
**[02:50]** your AI provider, whether that be OpenAI  
**[02:53]** or Bedrock or Vertex AI from Google or  
**[02:55]** one of these that will give you language  
**[02:57]** models and such. And your agent will  
**[02:59]** have tools that it can grab with MCP or  
**[03:01]** whatever else. And you have uh your data  
**[03:04]** here which can be unstructured or  
**[03:05]** structured data. Um unstructured coming  
**[03:08]** from documents and then structured data  
**[03:09]** coming from things like relational  
**[03:11]** tables or CSV files or or what have you.  
**[03:14]** Um and so when you put a knowledge graph  
**[03:16]** in the middle here, basically what  
**[03:18]** you're able to do is expose a lot of  
**[03:21]** context around how your data is  
**[03:23]** structured. um that allows an agent to  
**[03:25]** sequence things in either a multihop  
**[03:27]** behavior or construct queries or graph  
**[03:30]** patterns that makes it basically optimal  
**[03:33]** to fit inside of the context window. And  
**[03:35]** I'll show you what that looks like a  
**[03:37]** little bit here uh through a demo. Um  
**[03:40]** basically the demo that I'm going to  
**[03:42]** show you um we'll take an example from  
**[03:45]** an employee and talent agent. So, I've  
**[03:48]** prepared some dummy data, uh, some  
**[03:50]** resumeé data, and the employee agent  
**[03:52]** will be responsible for assisting with  
**[03:54]** skills analysis, talent search, and some  
**[03:57]** stuff with collaboration and teams  
**[03:59]** review.  
**[04:00]** So, um, if I go ahead and look at the  
**[04:03]** source data here, uh, we have this data  
**[04:06]** right now contained inside of a bunch of  
**[04:08]** résumés. Um, so I have about 30 résumés  
**[04:10]** here, um, that just sort of, you know,  
**[04:12]** list things in plain text. And what  
**[04:15]** comes up really quickly is if we just  
**[04:16]** take these ré texts and parse them and  
**[04:20]** uh put a vector index on them and just  
**[04:22]** search them with vectors, we'll find  
**[04:23]** very quickly that we don't really get  
**[04:26]** what we need. Um so I have a notebook  
**[04:28]** here that's demonstrated that where  
**[04:31]** basically um even simple questions if I  
**[04:33]** just ask a question like how many Python  
**[04:35]** developers I have right in my in my set  
**[04:38]** of uh people um all that it can really  
**[04:41]** do is search for Python developer from  
**[04:44]** the text right using something like  
**[04:46]** semantic search and uh it will tell me  
**[04:49]** that I have five Python developers  
**[04:51]** because it will hit the limit on the  
**[04:53]** number of documents it could take so  
**[04:55]** really only get five resumes back. So  
**[04:57]** there's ways that you can work with  
**[04:59]** metadata, right, to kind of document  
**[05:00]** metadata to to work around that and  
**[05:03]** maybe get a better answer. Um, but not  
**[05:05]** all questions are that easy. For  
**[05:07]** example, um, if I asked here for  
**[05:10]** something like summarize uh, my  
**[05:12]** technical talent and skills  
**[05:13]** distribution, again, all the agent can  
**[05:16]** really do with a vector search tool is  
**[05:18]** plug these generic search terms like  
**[05:21]** technical skills and programming  
**[05:22]** languages. And so while it may get a  
**[05:25]** response back, this response is likely  
**[05:28]** not going to be accurate. It's not going  
**[05:29]** to be complete. Um because it's just the  
**[05:32]** five top résumés that happen to match  
**[05:35]** that generic search criteria the best.  
**[05:37]** Um, and so basically what ends up  
**[05:40]** happening is, you know, regardless of  
**[05:43]** how sophisticated a language model or  
**[05:47]** how advanced a platform or framework,  
**[05:50]** you know, agent building framework that  
**[05:52]** we try to throw against this, we're not  
**[05:54]** going to be able to scale with just  
**[05:55]** vector search. We're going to run into  
**[05:56]** problems. And the core problem is really  
**[05:59]** that we're not managing and organizing  
**[06:02]** our context and our data in a way that  
**[06:04]** an LLM can pull efficiently. And so we  
**[06:07]** can fix this problem with a knowledge  
**[06:10]** graph basically to organize and manage  
**[06:12]** the data so that we can get that context  
**[06:15]** and pull the right information in.  
**[06:18]** So what I'll show you here um if I go  
**[06:21]** over to Neo forj get rid of some of the  
**[06:24]** queries that I was running earlier um  
**[06:27]** and me make this a little bit bigger for  
**[06:30]** you so you can see. Uh so I've gone  
**[06:33]** ahead and loaded this data and I'll talk  
**[06:34]** about that in a second. Um, but I wanted  
**[06:37]** to talk to you a little bit about the  
**[06:38]** schema that we're going to make from  
**[06:40]** those résumés.  
**[06:42]** So,  
**[06:44]** here's the schema. Um, and we can start  
**[06:46]** simple with these schemas. Uh, we're  
**[06:49]** basically going to take our documents  
**[06:50]** and extract entities into this schema.  
**[06:53]** And you don't have to migrate all of  
**[06:55]** your data right away, by the way, if  
**[06:56]** you're starting outside of a graph  
**[06:58]** database. You can start small with a  
**[07:00]** very simple schema like this and then  
**[07:02]** build on it later. So, there's no need  
**[07:03]** to migrate everything right away. Um but  
**[07:05]** basically all I'm going to say is I'm  
**[07:06]** going to have person nodes and those  
**[07:09]** people are going to know different  
**[07:10]** skills which is another node and nodes  
**[07:13]** is a relationship and then those people  
**[07:16]** are also going to be able to accomplish  
**[07:18]** various types of projects or things. So  
**[07:20]** publish, build, win, manage etc. And  
**[07:23]** those things can exist inside of  
**[07:25]** different work domains and be of  
**[07:27]** different work types. Um and all of the  
**[07:30]** code that I use for this I'll link to  
**[07:32]** the repository later um in the deck.  
**[07:34]** I'll give you a QR code for it so you'll  
**[07:35]** be able to get to all of it. Um, but we  
**[07:37]** basically perform entity extraction and  
**[07:39]** put this information inside of a graph  
**[07:41]** database.  
**[07:43]** And uh the what that looks like uh once  
**[07:47]** it's done is kind of like this. So this  
**[07:51]** is uh just a sample of the data. But you  
**[07:54]** see here we'll have our people which  
**[07:56]** will have uh uh text from the resume as  
**[08:00]** well as an embedding for vector search  
**[08:02]** and some other metadata. Um those people  
**[08:05]** will have skills as you see here like  
**[08:07]** leadership uh we have project management  
**[08:10]** we have SQL here um team management all  
**[08:13]** of these things um that connect them  
**[08:15]** together connect between multiple people  
**[08:18]** and then we also have these projects  
**[08:20]** that people work on um and those are  
**[08:23]** connected by the domains so for example  
**[08:26]** DevOps and cloud um as well as different  
**[08:29]** work types so infrastructure  
**[08:32]** system a project etc. Connecting all  
**[08:35]** this data together and once we have data  
**[08:37]** in this format we can do something  
**[08:39]** called pattern matching using cipher  
**[08:41]** which is our query language to pull that  
**[08:43]** data back in a in a logical way. So for  
**[08:45]** example um  
**[08:48]** I can do a pattern like this in cipher  
**[08:51]** which is basically saying hey find  
**[08:52]** people who have built uh different  
**[08:55]** things or projects inside of different  
**[08:57]** domains and I just limit it to the first  
**[08:59]** 20 here just so we can visualize it and  
**[09:01]** you'll see here we'll get our people um  
**[09:05]** build right different projects and those  
**[09:09]** projects are in different domains. You  
**[09:11]** see there's a couple different examples  
**[09:12]** here.  
**[09:14]** Um, and effectively we can make this  
**[09:17]** logic available to any AI system through  
**[09:21]** our MCP server for Neo Forj or really  
**[09:24]** any MCP tooling, right? And that's where  
**[09:26]** we're able to make all of this context  
**[09:28]** available and boost our explanability  
**[09:30]** and our accuracy. So to demonstrate  
**[09:32]** that, I'll show you what that looks like  
**[09:34]** inside of Claude. Um,  
**[09:38]** slide over this way.  
**[09:40]** Um and basically with claude I've taken  
**[09:44]** our MCP server for Neo forj I've called  
**[09:47]** it employee cipher tools and I've  
**[09:49]** configured it to get the schema um and  
**[09:52]** run cipher here. Um so basically the two  
**[09:57]** uh types of tools that are available  
**[09:59]** right is to get the schema of the graph  
**[10:01]** um and then to execute those cipher  
**[10:03]** queries those pattern matching  
**[10:04]** capabilities. And so now what happens is  
**[10:07]** if I want to ask a question um for  
**[10:11]** example here let me take my Python  
**[10:14]** developer headcount question  
**[10:18]** find it  
**[10:26]** over here.  
**[10:31]** And if I go ahead and ask that question,  
**[10:34]** what will happen is it will think about  
**[10:35]** this for a little bit. Um, and then the  
**[10:38]** first thing it should do is get the  
**[10:39]** graph schema which we see here.  
**[10:45]** So you can see the text which is  
**[10:47]** basically that schema that I was showing  
**[10:49]** before when I first went into the  
**[10:50]** console. And then now it's going to look  
**[10:53]** for the number of employees.  
**[10:55]** You can see the pattern matching here  
**[10:57]** for the number of employees. And then  
**[11:00]** you'll see it comes back. It tells me I  
**[11:01]** have 28 employees that know Python,  
**[11:03]** which for this data set is the correct  
**[11:05]** answer. I I went ahead and validated  
**[11:07]** that before this. Um and then you see  
**[11:09]** that it will actually explain its logic  
**[11:11]** and it can explain it on a very  
**[11:13]** technical level. Um this is exactly how  
**[11:15]** I query the data. It's just in natural  
**[11:17]** language explaining the query that it  
**[11:18]** used and then it will list you know all  
**[11:21]** the developers um and then potentially  
**[11:24]** uh other insights that it has down here.  
**[11:26]** Um, and what gets really interesting is  
**[11:28]** when you start asking those more  
**[11:30]** complicated questions like this one that  
**[11:32]** we had before about summarizing  
**[11:35]** the technical talent and skills  
**[11:37]** distribution, it can actually start  
**[11:39]** chaining these commands together. So  
**[11:41]** it's not just going to write one cipher  
**[11:43]** query, but just because of the way a  
**[11:45]** natural language has kind of a chain of  
**[11:46]** thought reasoning. Um the the language  
**[11:50]** model has chain of thought reasoning in  
**[11:52]** this case. You can sort of think about  
**[11:55]** having multiple of these queries fire  
**[11:56]** off at once. So you'll see here I'll  
**[11:58]** look for persons knowing skills. Um and  
**[12:02]** then it will look for people, you know,  
**[12:04]** accomplishing different things here. um  
**[12:07]** going on and on sort of uh down the list  
**[12:10]** uh looking at different work types um  
**[12:12]** and then it's going to go ahead and  
**[12:13]** create a graphic and this might take a  
**[12:15]** while but it's basically going to make  
**[12:16]** an interactive uh dashboard for us. Um  
**[12:20]** so again right we were able to  
**[12:22]** accomplish all of this simply by having  
**[12:25]** this MCP tooling available um through  
**[12:28]** sort of our official MCP for Neo forj uh  
**[12:32]** product offering and then having all of  
**[12:35]** that context in the graph with a schema  
**[12:37]** and the cipher pattern matching  
**[12:39]** capability.  
**[12:40]** So we'll give it a second here uh to  
**[12:42]** come back. This might just take a minute  
**[12:44]** for it to to spit out all the code it  
**[12:46]** needs uh for the visualization.  
**[12:50]** And here we go. So we get our visual  
**[12:53]** back right with the total number of  
**[12:54]** employees, key insights, top technical  
**[12:57]** skills at the company, department  
**[12:59]** distributions. We [clears throat] can  
**[13:01]** look at the uh project domains that we  
**[13:03]** have the different work types. Um and it  
**[13:06]** should give me a written summary here  
**[13:08]** again explaining all the retrieval  
**[13:10]** logic. So we have this explanability  
**[13:12]** component now because everything's sort  
**[13:14]** of symbolically represented in this  
**[13:16]** graph. Um and we basically get  
**[13:18]** everything that we need right to start  
**[13:21]** answering these questions uh much more  
**[13:23]** accurately.  
**[13:26]** Um so you know that is really cool just  
**[13:29]** by itself again using that MCP for Neo  
**[13:33]** Forj uh server.  
**[13:36]** And now what I want to talk about is  
**[13:40]** how we can build on this even further  
**[13:42]** when we think about Aura agents. So, I'm  
**[13:44]** going to talk about uh the next product  
**[13:47]** in our lineup here  
**[13:49]** and Aura agents. So, I had to sum it up  
**[13:52]** in one sentence. What this allows you to  
**[13:54]** do is build intelligent agents that are  
**[13:56]** grounded in your Aura DB knowledge  
**[13:58]** graphs with an endtoend um agent  
**[14:02]** creation platform. So, basically from  
**[14:05]** building to testing to deploying  
**[14:07]** everything, you can do all of that in  
**[14:08]** minutes inside of a low code no code  
**[14:10]** interface that we'll go over in a  
**[14:11]** second. And it sort of seamlessly  
**[14:14]** integrates sort of the retrieval and  
**[14:16]** reasoning logic that we were just going  
**[14:17]** over on your data. And because we handle  
**[14:20]** all the infrastructure for you,  
**[14:22]** everything from the agent to the  
**[14:24]** embedding calls and all this sort of  
**[14:26]** stuff, it greatly simplifies your AI  
**[14:28]** stack and your AI ops.  
**[14:30]** Um, and specifically, uh, the key  
**[14:33]** components, right, is really being able  
**[14:34]** to create the agent through that low  
**[14:36]** code, no code, uh, builder. um having  
**[14:40]** different retrieval tools um which we'll  
**[14:42]** go over which is cipher templates vector  
**[14:44]** search and text to cipher having a  
**[14:47]** playground to test the agent um and then  
**[14:50]** being able to deploy the agent and  
**[14:51]** access it through an API and right now  
**[14:53]** the uh agent deployment is available  
**[14:56]** through a REST API um there's an Aura  
**[14:59]** API endpoint uh that we have so Aura API  
**[15:02]** is something that exists for just  
**[15:03]** managing your Aura instances inside of  
**[15:06]** the cloud which are is our fully managed  
**[15:08]** cloud offer offering for Neo forj  
**[15:09]** databases. Um, and MCP support for that  
**[15:12]** is going to come soon. Although you can  
**[15:14]** wrap this very easily inside of an MCP  
**[15:16]** server and and I'll show you how to do  
**[15:18]** that here um in the next few minutes or  
**[15:21]** so. So,  
**[15:26]** oops. Not sure what happened there.  
**[15:29]** Um, let's see.  
**[15:32]** All right. So, we'll move on to our  
**[15:36]** to our demo now.  
**[15:39]** Um,  
**[15:42]** if I go back, I'll open up this window.  
**[15:45]** So, basically what I'll do is you'll see  
**[15:48]** an agent that's already created here,  
**[15:50]** but I'll go to my uh agents tab and I'll  
**[15:52]** just start creating an agent. So there's  
**[15:56]** this, if you have the early access,  
**[15:58]** there's this agent preview here. And I  
**[16:01]** can go ahead and select create. And I  
**[16:04]** can just start building this agent  
**[16:06]** inside inside of Aura. So I can say um I  
**[16:09]** want maybe an employee agent. We'll say  
**[16:12]** employee agent 3. Um so that it  
**[16:15]** deconlicts with the other ones that I  
**[16:17]** have. I've done this a couple times. I  
**[16:19]** have a pre-prepared one as well. um or  
**[16:23]** agent  
**[16:25]** three.  
**[16:27]** Um and we'll call it employee agent  
**[16:31]** here.  
**[16:34]** And then I can go ahead and add a  
**[16:36]** description,  
**[16:39]** conduct skills and talent search and  
**[16:41]** such.  
**[16:42]** And then I can go ahead and add prompt  
**[16:45]** instructions. Um, so if you're familiar  
**[16:47]** with building agents, you'll know that  
**[16:49]** uh there's this thing called a system  
**[16:50]** prompt, right? Um, that just tells it  
**[16:53]** basically general instructions on how to  
**[16:56]** behave. So all the stuff in here um is  
**[16:58]** just telling it kind of what's in the  
**[17:00]** knowledge graph and then how to use some  
**[17:02]** of the tools that it has. I can go ahead  
**[17:04]** and select a target instance. Um, we'll  
**[17:07]** go ahead and use the same graph that we  
**[17:08]** were looking at earlier, which is this  
**[17:10]** employee graph. Um, I'm going to go  
**[17:13]** ahead and select external. Um, internal  
**[17:16]** will basically mean that I can test it  
**[17:17]** through this UI continuously. When I say  
**[17:20]** external, it just makes it available as  
**[17:22]** an endpoint. So then I can use it in  
**[17:24]** downstream systems.  
**[17:26]** Um, and then I can go ahead and start  
**[17:27]** adding tools. I need to add at least one  
**[17:29]** tool to try this out. And I can start  
**[17:32]** with something simple. So for example,  
**[17:34]** similarity search, which I think a lot  
**[17:36]** of people are already familiar with. And  
**[17:38]** I can just say, hey, I want to create a  
**[17:40]** resume search tool. And I am going to  
**[17:43]** give it a description  
**[17:47]** for example like this. Search résumés uh  
**[17:51]** using semantic similarity to identify  
**[17:53]** and retrieve potentially relevant info  
**[17:55]** and associate metadata on the person. I  
**[17:58]** have a warning not to use this uh for  
**[18:00]** counting and aggregation. This is just  
**[18:02]** for the uh language model. when it sees  
**[18:05]** this um it will uh basically use this  
**[18:08]** information to select the tool and then  
**[18:10]** figure out how to appropriately use the  
**[18:11]** tool afterward. Um and  
**[18:15]** the uh embedding provider in this case  
**[18:17]** we used open AI with our data and text  
**[18:21]** embedding ADA. So these are you know  
**[18:24]** sort of free of charge. These get called  
**[18:26]** uh at query time to go ahead and search  
**[18:29]** uh the database with vector search. And  
**[18:32]** then the index name I believe for this  
**[18:35]** one is  
**[18:37]** text embeddings. And we'll go ahead and  
**[18:40]** do top KF5 just as an example. Um the  
**[18:44]** language model that we use by the way  
**[18:45]** here is Gemini 2.5 flash. And uh that's  
**[18:50]** offered out of the box. So it's not like  
**[18:52]** you have to have your own model provider  
**[18:54]** um that you configure with this. We have  
**[18:56]** a model provider in here. Um and that's  
**[18:58]** just the model that's used. So you don't  
**[19:00]** have to worry about that side of the  
**[19:01]** infrastructure. Um and now that I have  
**[19:03]** that tool, right, I can ask a question  
**[19:06]** like I can say, hey, this is sort of the  
**[19:08]** playground uh testing UI. Um I can ask  
**[19:12]** which résumés speak to strong AI skills?  
**[19:16]** And when I do that, it will think for a  
**[19:18]** while. Um, and then eventually it should  
**[19:20]** come back with a response hopefully  
**[19:22]** using uh the tool that the one tool that  
**[19:25]** I have here. Um and you'll see it says  
**[19:28]** based on the resume search and then it  
**[19:30]** will bring back an explanation and you  
**[19:32]** know a a set of um people here and um it  
**[19:38]** brought back five people and you'll see  
**[19:41]** here um there's an explanation right if  
**[19:44]** when it says thinking where you can see  
**[19:46]** the reasoning so I see the reasoning it  
**[19:48]** says hey it asked to find résumés it  
**[19:51]** knew to use well it only had one tool  
**[19:53]** right but it knew in this case to use  
**[19:54]** the ré search tool Here's the input it  
**[19:56]** had and then you can see the output and  
**[19:59]** then um any other logic or reasoning  
**[20:01]** that it did after that. So all that's  
**[20:03]** exposed and it's exposed to the API as  
**[20:06]** well. So we maintain that explanability  
**[20:08]** um going all the way uh to the end user  
**[20:10]** application. Um and I can add other  
**[20:13]** tools here too, right? So I can go ahead  
**[20:15]** and for example add a tool around text  
**[20:19]** to cipher. Um text to cipher is we  
**[20:23]** actually used a fine-tuned version of  
**[20:25]** Gemini for this um that's specifically  
**[20:28]** tuned to generate cipher again our query  
**[20:30]** language um based on natural language  
**[20:34]** responses and uh for this one you know I  
**[20:37]** can add extra description to kind of  
**[20:41]** guide it on hey when should I use this  
**[20:43]** tool in this case I'll give it a pretty  
**[20:46]** generic one to just answer free form  
**[20:48]** questions um but I could sort of direct  
**[20:51]** uh the agent here to only use this in  
**[20:53]** certain scenarios or as a fallback. Um  
**[20:56]** because these things are sort of  
**[20:58]** dynamic. They have a stoastic element to  
**[21:00]** them. Um but anyway, I'm just going to  
**[21:02]** use a very generic uh prompt here to  
**[21:05]** just hey for free form questions and for  
**[21:07]** aggregations basically.  
**[21:09]** Um and then once I save that, you'll see  
**[21:12]** it'll it'll show up here. both these  
**[21:14]** tools will um and then I can ask a  
**[21:16]** question like which you know a good  
**[21:19]** aggregation question here might be hey  
**[21:21]** which people have worked on the most  
**[21:23]** things or projects  
**[21:26]** and then it'll think for a while and  
**[21:28]** then hopefully right it will be able to  
**[21:31]** figure out that it needs to select uh  
**[21:33]** this query graph tool to perform that  
**[21:35]** aggregation  
**[21:36]** um you'll see here that it uh went ahead  
**[21:39]** and did some some form of aggregation  
**[21:41]** here to pull people back so I suspect  
**[21:43]** And if we look here, you'll see it used  
**[21:46]** the right tool and it um basically gave  
**[21:50]** some input to this tool to then generate  
**[21:54]** this uh pattern here to match people who  
**[21:57]** have you know all these relationship  
**[21:59]** size one built led managed just like we  
**[22:00]** saw in the schema basically worked on  
**[22:03]** things and then go ahead and count that  
**[22:05]** um and return um by the names and you'll  
**[22:08]** see here uh this is the output that it  
**[22:10]** got. very simple.  
**[22:12]** Now, what gets really exciting about  
**[22:14]** this as well is that we can start to add  
**[22:17]** here um what are called uh cipher  
**[22:20]** templates. And because I'm going to fat  
**[22:22]** thumb that when I do this live, I've  
**[22:24]** prepared another agent where I've filled  
**[22:26]** that in already. Um but an interesting  
**[22:29]** scenario that we can look at for this uh  
**[22:32]** would be something like I'm going to  
**[22:34]** plug in some parameters. These are just  
**[22:35]** going to save um some ids.  
**[22:38]** Uh but basically uh figure out how are  
**[22:42]** people similar, right? So if I wanted  
**[22:44]** to, for example, in the context of in an  
**[22:46]** employee or HR scenario, find back fills  
**[22:48]** for someone uh for example, um I can  
**[22:52]** say, okay, well, I want to identify a  
**[22:54]** pattern where if I have two people, find  
**[22:57]** all the ways that they're similar  
**[22:58]** according to my graph. And the great  
**[23:01]** thing about cipher and graphs is that I  
**[23:03]** can have these flexible patterns where I  
**[23:05]** say, "Hey, just traverse over zero to,  
**[23:08]** you know, one basically one to four hops  
**[23:10]** effectively um without going over  
**[23:12]** another person and just count like all  
**[23:14]** of the different ways that these people  
**[23:16]** are similar." So you can see with these  
**[23:18]** two people basically  
**[23:21]** um I can go ahead and see that I get you  
**[23:26]** know two people and then I get the  
**[23:28]** skills that are similar here and then I  
**[23:30]** get projects that they've worked on  
**[23:32]** inside of common domains and uh common  
**[23:35]** work types and that can be very useful  
**[23:37]** for when you need subject matter  
**[23:39]** expertise inside of the tool. So rather  
**[23:41]** than just relying on v on vector search  
**[23:43]** which could be opaque here I've actually  
**[23:45]** broken this down inside of a graph I can  
**[23:47]** score this in various ways. I can count  
**[23:49]** like the number of hops and  
**[23:51]** relationships which I do in inside of  
**[23:52]** this tooling um that I'll show you here  
**[23:55]** in just a second. uh and that will allow  
**[23:57]** me to return, you know, pretty  
**[23:59]** sophisticated responses that are well  
**[24:01]** validated, right? And this logic is  
**[24:04]** flexible so that if I change or adjusted  
**[24:06]** my data model, I have a flexible schema  
**[24:08]** and a query language that would  
**[24:09]** accommodate new types of nodes, right?  
**[24:11]** Being added in between them. Um so  
**[24:13]** there's nothing restricting them to just  
**[24:15]** uh work types or just skills or or  
**[24:17]** whatnot. Uh so basically  
**[24:20]** go ahead and save this guy and then exit  
**[24:22]** out. I have my original employee agent  
**[24:26]** and I will go ahead and press edit just  
**[24:29]** so you can see um where I've filled in  
**[24:33]** the find similar persons um where I have  
**[24:36]** that query pattern that does the  
**[24:37]** scoring. It basically just counts, you  
**[24:40]** know, the number of paths between  
**[24:42]** people. And then I have my find  
**[24:44]** similarities uh between people here,  
**[24:48]** which is similar to the one I was just  
**[24:50]** showing you. And it serializes the  
**[24:52]** information. So it basically will in  
**[24:54]** text kind of explain to um the agent how  
**[24:59]** exactly two people are similar uh  
**[25:02]** according to the graph. And because I  
**[25:05]** have this public endpoint available, um,  
**[25:08]** if I go into our blog here that we  
**[25:10]** recently wrote,  
**[25:12]** uh, there's an explanation if I go down  
**[25:15]** towards the bottom  
**[25:18]** of,  
**[25:20]** um, basically how to call that endpoint.  
**[25:23]** Um, and as well there's this step that  
**[25:28]** will explain um, through model context  
**[25:31]** protocol here. uh basically um how you  
**[25:36]** can uh create a server that will uh call  
**[25:41]** that endpoint, an MCP server that will  
**[25:43]** call that endpoint, which is exactly  
**[25:45]** what I did.  
**[25:47]** And uh what that allowed me to do is if  
**[25:50]** I go back um to my cloud window here,  
**[25:54]** I've gone ahead and uh created this  
**[25:57]** tool, which I'll turn on now, and this  
**[25:59]** will call that aura agent endpoint. Um,  
**[26:02]** so I'm making it available to claw. Now  
**[26:04]** we now have a multi- aent system where  
**[26:05]** I'm calling this upstream uh graph  
**[26:07]** agent. And uh the only one thing that I  
**[26:11]** did here is um inside of my settings uh  
**[26:15]** just for transparency here the you  
**[26:17]** there's this profile setting inside of  
**[26:19]** Claude which is like Claude's system  
**[26:20]** prompt almost or information that that I  
**[26:23]** guess uh gets you know uh added to its  
**[26:26]** system prompt so to speak. um where I  
**[26:29]** can say, hey, prioritize using expert  
**[26:31]** agents uh where you can. And then I also  
**[26:33]** added um some extra stuff in here to  
**[26:36]** help it surface the retrieval logic so  
**[26:38]** we could see that earlier. But um I  
**[26:41]** added to prioritize using expert agents  
**[26:43]** where they're available. And I've named  
**[26:44]** my MCP server, you know, an expert agent  
**[26:46]** tool when I configured it uh with  
**[26:48]** Claude. So basically, let's go back to  
**[26:51]** our uh original window here. Give it  
**[26:54]** some time to load. Um, and yes, this is  
**[26:58]** where we were before. This was our  
**[27:01]** visual. Um, so basically now I can go  
**[27:05]** ahead and ask a similarity question like  
**[27:08]** who is most similar to Lucas Martinez  
**[27:10]** and why he exists inside of our  
**[27:13]** database?  
**[27:15]** Um, and it will hopefully think about  
**[27:18]** this and then it will use our expert  
**[27:20]** agent here to pull that information  
**[27:22]** back.  
**[27:25]** In this case, it's going to go for  
**[27:27]** running cipher.  
**[27:28]** Sometimes that happens with agents.  
**[27:38]** Now, it's going to call the agent. So,  
**[27:39]** it's interesting, right? It Let's see  
**[27:41]** what it did. it um it looked like it  
**[27:45]** called to like get all the information  
**[27:47]** from him in the graph, but then it  
**[27:49]** realized, oh, I should probably call the  
**[27:51]** the Aura agent because it was sort of in  
**[27:53]** my prompts to uh go ahead and do that.  
**[27:56]** It's backwards, but it's working. So,  
**[27:58]** let's see what it comes up with here.  
**[28:19]** This is going to go for some more  
**[28:21]** details, but we can look at what the  
**[28:23]** Aura agent call looked like. So, it  
**[28:25]** asked the question here. Um, and then  
**[28:27]** you can see that the Aura agent was  
**[28:30]** calling those find similar people. Um,  
**[28:34]** and then find similarities between  
**[28:37]** people. So it called those same cipher  
**[28:39]** templates that we wanted it to call  
**[28:41]** there. Um and you can see it it sort of  
**[28:45]** scored everyone um according to the  
**[28:48]** graph logic that we had. It explains its  
**[28:51]** retrieval logic and then it it basically  
**[28:53]** says here's the most similar person that  
**[28:55]** in theory you could you could backfill  
**[28:57]** this person with and it explains the  
**[28:58]** skills similar work profiles. We saw the  
**[29:01]** system and product stuff in the last  
**[29:03]** query. Um, so very interesting kind of  
**[29:05]** how you can have that all deployed right  
**[29:08]** through that Aura agent. You can use the  
**[29:10]** Aura agent by itself or like I showed  
**[29:12]** here, you can use it inside of a multi-  
**[29:14]** aent uh system.  
**[29:17]** All righty. So, let's go ahead and wrap  
**[29:19]** up because I think we're like uh very  
**[29:21]** very very close to time here.  
**[29:25]** So, um in summary, right, with Aura  
**[29:28]** agents, we have this low noode uh agent  
**[29:32]** creation. We saw the admin UI that you  
**[29:34]** could set up, how you can test and  
**[29:36]** deploy it. That deployment has, you  
**[29:39]** know, it's all authenticated through the  
**[29:41]** Aura API, so it's secure. There's a  
**[29:43]** client um secret and token and all that  
**[29:45]** sort of stuff. Um we saw the different  
**[29:48]** types of graph data retrieval tools uh  
**[29:50]** between the cipher templates, the  
**[29:52]** similarity search and the text to  
**[29:53]** cipher. Um the text embeddings that were  
**[29:56]** supported, we have OpenAI um and Google  
**[29:58]** Gemini as well. There's more to come  
**[30:00]** later. the testing UI and then the  
**[30:02]** endpoint uh that we saw that got um that  
**[30:05]** got shipped um and we were able to call  
**[30:08]** through our MCP server. Um and this will  
**[30:10]** be available in Aura free professional  
**[30:13]** and business critical tiers. Um so some  
**[30:16]** resources for you to check out. Um we  
**[30:19]** have a new web page uh which I'm biased  
**[30:22]** because I helped make it but I think  
**[30:24]** it's great. It it goes over a lot of  
**[30:25]** very general um sort of resources and  
**[30:28]** kind of explains some of the context  
**[30:30]** stuff. It has links to uh Graph Academy  
**[30:32]** and a bunch of other places where you  
**[30:34]** can go and learn more, get different  
**[30:35]** blogs and stuff like that. For Aura  
**[30:38]** Agent uh in specifically on October  
**[30:41]** 25th, we'll have a uh virtual workshop  
**[30:45]** uh in Road to Node. So, that'll be a  
**[30:46]** great one to check out if you want like  
**[30:49]** a much longer period of time to really  
**[30:51]** sit through and learn how to build these  
**[30:52]** agents and get more in depth with them.  
**[30:54]** Um tutorials in GitHub are here,  
**[30:57]** including the example that I just went  
**[30:58]** over. um and a couple other examples as  
**[31:01]** well. And then there's a technical blog  
**[31:03]** that goes over a lot of the stuff that I  
**[31:05]** just went over, but with um a different  
**[31:07]** uh con contracts agent example. Um for  
**[31:10]** the MCP server, you can get that through  
**[31:12]** GitHub. Um there's directions there on  
**[31:15]** how to configure it. It's all written in  
**[31:17]** Go. I think there's a binary that you  
**[31:19]** can just get um and just you can use it  
**[31:22]** automatically um for whatever your  
**[31:23]** operating system is. Um I have an  
**[31:26]** example in GitHub. So this will link to  
**[31:28]** all the code that I use for the entity  
**[31:30]** extraction and all that stuff in the  
**[31:32]** graph that I was showing you. Um and  
**[31:34]** then of course in Neo Forj Labs we  
**[31:36]** actually have um much more different  
**[31:38]** types of capabilities. So we have like  
**[31:40]** data modeling and um and even like graph  
**[31:45]** data science stuff, graph analytics. So  
**[31:47]** there's other MCP servers that are in  
**[31:49]** labs um that are more experimental which  
**[31:51]** we haven't taken into core product yet.  
**[31:53]** So if you wanted to explore that um that  
**[31:55]** that's very interesting as well.  
**[31:57]** So, that is all I have for you today.  
**[32:00]** Hopefully, this was informative. Um, and  
**[32:03]** yeah, I'm excited. Hopefully you're  
**[32:04]** excited, too. Thank you everyone. Have a  
**[32:07]** great day.  
**[32:10]** [music]  