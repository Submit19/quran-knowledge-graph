# Transcript: https://www.youtube.com/watch?v=sBf8TJgqdwY

**Language:** English (auto-generated) (en) — auto-generated
**Snippets:** 652

---

**[00:09]** Thank you very much. Hey everyone. Um,  
**[00:12]** thanks for joining. Good to good to see  
**[00:15]** everyone at nodes. Um, I think I think I  
**[00:18]** have been uh a part of every node since  
**[00:20]** they started. So that's super fun. Um, I  
**[00:23]** dropped a link to the the slides in the  
**[00:26]** chat here. Um, feel free to grab those.  
**[00:28]** There's some links and um resources that  
**[00:32]** you might find useful. You also scan the  
**[00:34]** that QR code. Uh so my name is Will. I  
**[00:37]** work on the product team at Neoraj uh  
**[00:41]** with a focus on AI innovation  
**[00:44]** initiatives. Um some folks might might  
**[00:47]** have seen me around the NearJ community  
**[00:48]** before. I I used to work on the  
**[00:51]** developer relations team for a while and  
**[00:53]** then uh the last two years I've been uh  
**[00:56]** working in a few different AI startups  
**[00:58]** and uh recently back to to NearJ on the  
**[01:00]** the product team. So good to see  
**[01:03]** everyone there. There's some links uh to  
**[01:05]** get a hold of me too if you want to feel  
**[01:07]** free to uh to reach out. Happy to chat  
**[01:09]** with folks. So the the title of this  
**[01:12]** when when I pitched it was the fastest  
**[01:14]** path to building an agent for your  
**[01:15]** knowledge graph is is by using Neo forj.  
**[01:18]** That was several months ago when when I  
**[01:20]** when I proposed it. I think um I think  
**[01:23]** now if I would say what's the fastest  
**[01:25]** path to building an agent for your  
**[01:27]** knowledge graph is by actually creating  
**[01:29]** an aura agent. Um I'm curious. Let me  
**[01:32]** know in the the chat. I'm really curious  
**[01:34]** like if anyone has tried Aura agent yet.  
**[01:38]** This is um still in preview but it's  
**[01:40]** available in Aura. Sign into the the  
**[01:42]** Aura console and you'll see it there. Um  
**[01:45]** this is a really neat way to create uh  
**[01:48]** agents that have tools. So uh text to  
**[01:53]** cipher tool. We can create cipher  
**[01:55]** templates or just really simple  
**[01:57]** similarity search uh and create a agent  
**[02:00]** that can access those tools that are  
**[02:03]** capable of quering your database and  
**[02:05]** then uh they're exposed an API. So, uh,  
**[02:08]** if I was going to build a talk, uh,  
**[02:10]** today about the fastest way to build an  
**[02:11]** agent for your knowledge graph, this is  
**[02:13]** probably the the route I would take. So,  
**[02:15]** um, definitely read the read this blog  
**[02:17]** post. I think Ed had a a talk today on  
**[02:20]** Ora agent. Um, I might be mistaken, but  
**[02:23]** but definitely, um, check that out if  
**[02:25]** you're interested in in creating agents  
**[02:27]** for uh, for your knowledge graph. So  
**[02:30]** really I think uh maybe a better way to  
**[02:32]** to frame this talk is we're going to  
**[02:34]** talk about MCP agents uh and graphs with  
**[02:37]** NeoRaj.  
**[02:39]** So we'll do a do a brief overview of of  
**[02:42]** NeoRaj um are folks familiar with with  
**[02:46]** NearJ I see um or sorry are folks  
**[02:50]** familiar with with MCP is rather what I  
**[02:52]** meant to say. I see a few folks in the  
**[02:53]** chat say that they did the training  
**[02:55]** yesterday for our agent. Cool. That's  
**[02:58]** awesome. U but yeah, let us know in the  
**[03:00]** chat. Uh we can kind of level set there  
**[03:03]** on on MCP, but then really I want to  
**[03:05]** talk about, you know, the the NearJ MCP  
**[03:08]** ecosystem. Uh how we can use MCP servers  
**[03:12]** that can connect to Neoraj for uh  
**[03:16]** different uh different ways to use those  
**[03:18]** with agents. And then we'll look at how  
**[03:19]** we can build your own MCP server. Uh and  
**[03:21]** then of course we'll we'll talk about  
**[03:22]** some of the challenges of of working  
**[03:24]** with uh MCP and and how to think about  
**[03:27]** that.  
**[03:28]** And you know feel free uh feel free to  
**[03:32]** uh keep the session as interactive as  
**[03:34]** possible. You know I can see the chat  
**[03:36]** here so you know feel free to drop that  
**[03:38]** in uh any questions or feedback thoughts  
**[03:40]** you have. There also some some Neo forj  
**[03:42]** folks uh in the chat as well.  
**[03:46]** Cool. So if we take a step back um this  
**[03:50]** blog post this was uh building effective  
**[03:53]** agents published by Anthropic almost a  
**[03:57]** year ago. post. I think this was  
**[03:58]** December of of last year and I think  
**[04:01]** this was a really influential blog post  
**[04:03]** to  
**[04:04]** kind of set different frameworks for how  
**[04:07]** to think about uh building agents and um  
**[04:10]** it goes deep into different patterns for  
**[04:12]** sort of multi- aent uh coordination and  
**[04:15]** and that sort of thing. But really I  
**[04:18]** think there's this this important  
**[04:19]** concept at the heart of of this idea of  
**[04:23]** an agent which is the augmented LLM,  
**[04:26]** right? So an LLM just has uh data  
**[04:30]** knowledge that it was trained on. Of  
**[04:32]** course we need to bring more recent more  
**[04:36]** relevant maybe private enterprise data  
**[04:38]** uh to the LLM. We also to have a true  
**[04:42]** agent the LLM needs to the agent rather  
**[04:46]** needs to be able to um understand and  
**[04:48]** interact with its environment and it  
**[04:51]** does this through the use of tools. Uh  
**[04:54]** so tools you can think of this as like  
**[04:56]** functionality functions that we've given  
**[04:59]** uh to our agent to be able to interact  
**[05:01]** with its environment.  
**[05:03]** If we extend that that concept a little  
**[05:05]** bit and and look at like what is a rough  
**[05:07]** architecture for uh your typical agent  
**[05:10]** look like it's something like this.  
**[05:11]** There's there's an orchestration  
**[05:14]** layer that's orchestrating like user  
**[05:16]** messages uh system prompts tool calls uh  
**[05:20]** with your LLM. Uh, how do we use tools?  
**[05:23]** Well, well, we use it to interact with  
**[05:25]** external services like maybe I'm  
**[05:27]** building an agent that has access to my  
**[05:30]** GitHub and is going to uh I don't know  
**[05:33]** post messages in in Slack when I uh do a  
**[05:37]** release or or something like that. Um,  
**[05:40]** retrieval is also an important piece of  
**[05:42]** this, right? how am I going to fetch  
**[05:45]** relevant data based on uh the user  
**[05:48]** message based on the query? Uh and that  
**[05:51]** also is done through tools. Uh the  
**[05:54]** ability for the agent to interact uh  
**[05:57]** with its environment. And now these  
**[06:00]** these tool calls so the the access to  
**[06:03]** tools models choosing to uh invoke the  
**[06:07]** tools that happens in the agent loop. Uh  
**[06:11]** this is typically a a three-stage loop.  
**[06:13]** You can think of this as the uh  
**[06:15]** typically called the a react loop. So  
**[06:17]** there's um reasoning  
**[06:20]** action and then observation as a result  
**[06:23]** uh of the action and then we go through  
**[06:24]** that loop again. Have we achieved the  
**[06:26]** goal? Can we um can we sort of respond  
**[06:30]** to the user in the loop? Uh no, we need  
**[06:33]** to maybe call another tool. Okay, we  
**[06:35]** have more information and we we reason  
**[06:37]** about that and and go through this loop.  
**[06:39]** And so when we're thinking of like the  
**[06:41]** definition or like the the heart of like  
**[06:43]** what is an agent, um Simon Willis uh  
**[06:46]** said, you know, an an LM agent runs  
**[06:49]** tools in a loop to achieve a goal. Uh  
**[06:52]** that's kind of how we think of it. And  
**[06:55]** that loop is really important when we  
**[06:58]** think about context. So context, this is  
**[07:02]** um like additional data that's passed to  
**[07:05]** the LLM when we want to uh invoke it.  
**[07:08]** And if we look on the the left side of  
**[07:10]** this diagram, right, without the the  
**[07:12]** sort of augmented LLM, we have a system  
**[07:15]** prompt and a user message. We send that  
**[07:18]** to uh to the model and we get back uh  
**[07:21]** some response. But now in this agent  
**[07:25]** loop where we have things like tool  
**[07:26]** calling, there actually might be a lot  
**[07:28]** in that context, right? we have uh tool  
**[07:30]** definitions. Uh maybe we have memory.  
**[07:34]** Maybe we have um like files and  
**[07:37]** documents that we want to to add into  
**[07:39]** the context. Um all of this sort of  
**[07:42]** starts to add up when we call those  
**[07:44]** tools. Well, the results of those tools  
**[07:47]** also go into the context and and so we  
**[07:48]** need to start thinking about uh managing  
**[07:51]** what's in our context. And this gave  
**[07:52]** rise to the this term context  
**[07:54]** engineering. Um, so regardless, I guess  
**[07:58]** I'm maybe sort of on the the left end of  
**[08:00]** of of this meme here, right? How do we  
**[08:02]** think about agents? Well, an agent is is  
**[08:04]** just an LLM uh calling tools in a loop  
**[08:08]** to achieve a goal.  
**[08:11]** And MCP uh is one of the ways that we  
**[08:14]** can expose tools uh to our agent. So  
**[08:19]** let's do a brief overview of of MCP. um  
**[08:22]** MCP model context protocol is a protocol  
**[08:27]** uh for exposing tools and and other  
**[08:30]** things. We'll talk about the other  
**[08:31]** things but think think of tools exposing  
**[08:33]** tools uh to our models. So the ability  
**[08:38]** to uh for the model to interact with and  
**[08:41]** understand uh its environment.  
**[08:44]** Early on MCP was referred to as like the  
**[08:47]** USBC uh of the the agent world and I  
**[08:51]** don't know that resonated I I think with  
**[08:53]** some folks. It's basically like a  
**[08:55]** standard interface when you're building  
**[08:58]** um an AI application is maybe a way to  
**[09:00]** think of it. So before MCP, we were all  
**[09:02]** sort of building our own sort of unique  
**[09:05]** bespoke APIs for interacting with  
**[09:07]** external services. uh MCP comes along  
**[09:11]** and we can just build that MCP server  
**[09:14]** once and then use that as an interface  
**[09:16]** to that service in all of our uh on all  
**[09:19]** of our AI applications. And even better  
**[09:22]** is that someone else maybe um GitHub for  
**[09:25]** example can build and publish an MCP  
**[09:27]** server and then we can use their  
**[09:29]** official MCP server uh to interact with  
**[09:33]** GitHub across all of our AI  
**[09:35]** applications.  
**[09:37]** So uh I copied this slide from the deep  
**[09:40]** learning.ai course. Um I think this is  
**[09:44]** uh this is a really good course that  
**[09:45]** goes a little bit deeper on you know  
**[09:48]** what MCP is, how do I how do I work with  
**[09:50]** it but also how do I build MCP servers.  
**[09:53]** So fundamentally um an MCP server  
**[09:56]** exposes uh tools, resources and prompt  
**[10:00]** templates. Mostly we're focusing on  
**[10:02]** tools. tools. These are, you know,  
**[10:04]** functions that the model can choose to  
**[10:07]** invoke uh to either fetch data, call an  
**[10:10]** API, something like that. Resources.  
**[10:13]** These are uh readonly data. Uh this  
**[10:15]** could be something like maybe a bunch of  
**[10:19]** example uh data models or example  
**[10:23]** um cipher queries that might be helpful.  
**[10:25]** And then the prompt templates, these are  
**[10:28]** kind of like prepackaged prompts that we  
**[10:30]** know uh work well. uh with sort of the  
**[10:35]** uh service that we're building the MCP  
**[10:36]** server for that our a application can  
**[10:39]** then uh can then use. There are also  
**[10:41]** lots of other interesting uh features  
**[10:43]** that are are in MCP like uh sampling  
**[10:46]** which allows us to uh to sort of send a  
**[10:50]** prompt back to another model. We can uh  
**[10:52]** sort of evoke and ask for specific  
**[10:55]** information. So definitely check out  
**[10:57]** this course um if you're interested in  
**[10:58]** MCP in general. What we're going to  
**[11:00]** focus on today is diving into like the  
**[11:03]** Neo Forj MCP ecosystem. So this landing  
**[11:07]** page, this is the um MCP page in the  
**[11:10]** developer guides, has information about  
**[11:14]** a bunch of different MCP servers. Um and  
**[11:17]** so it can be a little confusing and and  
**[11:20]** maybe overwhelming like which which MCP  
**[11:22]** server do I want? Um and roughly  
**[11:25]** speaking here there's docs for the um  
**[11:28]** official nearj supported MCP server and  
**[11:32]** then we have these near labs MCP servers  
**[11:35]** and this is an important distinction  
**[11:36]** like near labs these are uh more  
**[11:40]** experimental projects that allow us to  
**[11:44]** sort of build things put them out and  
**[11:45]** and validate them with the community.  
**[11:47]** These are not officially supported by  
**[11:49]** Neo forj. uh there there are a lot of  
**[11:54]** challenges and especially around  
**[11:56]** security and authorization with MCP. So  
**[11:58]** if you're uh if your requirements you  
**[12:01]** know need an officially supported uh and  
**[12:05]** uh MCP server look for the official MCP  
**[12:08]** server but then these NEFJ labs servers  
**[12:10]** these projects have um  
**[12:14]** maybe more experimental functionality  
**[12:16]** and there are a handful of those. We'll  
**[12:17]** talk about what some of those are in a  
**[12:18]** minute. And then there's uh  
**[12:20]** documentation on different framework  
**[12:22]** integrations like the Google MCP toolbox  
**[12:24]** for building MCP servers or integrating  
**[12:28]** uh MCP servers into all of the different  
**[12:30]** uh agent frameworks.  
**[12:33]** So the official MCP server uh this is  
**[12:36]** currently in uh beta. I think it's uh  
**[12:38]** beta 3 now. Earlier today um John and  
**[12:42]** Michael did a a talk that showed how to  
**[12:45]** use the uh official MCP server. Um, so  
**[12:48]** it's definitely functional. You can try  
**[12:50]** it out. Uh, there's some releases in the  
**[12:53]** GitHub repo there. The NJFJ cipher MCP  
**[12:56]** server. Um, this is the one we're going  
**[12:59]** to use today. This allows uh for  
**[13:02]** exposing the schema and also uh for our  
**[13:06]** model to be able to execute cipher  
**[13:09]** queries.  
**[13:11]** There's also the Nefrj data modeling MCP  
**[13:14]** server. um Jesus and and Alex did a a  
**[13:18]** talk earlier today using the data  
**[13:21]** modeling uh server to build an ontology.  
**[13:24]** So this is useful uh for creating data  
**[13:27]** models, visualizing them. This heavily  
**[13:30]** uses the resources feature. So there are  
**[13:32]** lots of uh example data models for uh  
**[13:36]** for different use cases. There's also  
**[13:39]** the Nej knowledger graph memory server  
**[13:42]** is one of the the labs MCP servers.  
**[13:44]** Memory is a really interesting topic. Um  
**[13:47]** we'll we'll talk a little bit about that  
**[13:49]** today. Uh memory is important for for  
**[13:52]** agents uh to be able to sort of hold  
**[13:54]** states and and knowledge across multiple  
**[13:57]** conversations or or interactions with  
**[13:59]** the user. Um entities uh entity  
**[14:02]** extraction and identifying facts and  
**[14:05]** preferences turns out to be quite quite  
**[14:07]** important. Um so this is an MCP server  
**[14:09]** that you can add to say like cloud  
**[14:11]** desktop for example uh which will be  
**[14:13]** able to build a knowledge graph um of  
**[14:15]** memories behind the scenes.  
**[14:18]** Let's take a look at uh a few things  
**[14:20]** like what can we do with the nearj MCP  
**[14:23]** server. Uh one is exploratory data  
**[14:27]** analysis. Um cloud desktop is a really  
**[14:30]** good MCP host application for this. Um  
**[14:33]** one because it has a really nice nice  
**[14:35]** interface. Um, and also because it has a  
**[14:39]** free version, uh, so we don't need to  
**[14:41]** pay for a subscription to be able to  
**[14:43]** test it out. This is the configuration  
**[14:46]** to add the, uh, near MCP server to  
**[14:51]** claude desktop. Um, basically what we're  
**[14:54]** using uvx here to run this python uh,  
**[14:58]** mcp near cipher package and then passing  
**[15:01]** in credentials to our neoj instance as  
**[15:04]** environment variables.  
**[15:06]** can take a look here. Um, here I've  
**[15:09]** added the Nefrj cipher MCP server to  
**[15:13]** cloud desktop in the configuration and  
**[15:17]** it shows up here. I I have a memory  
**[15:19]** server as well that I've disabled. But  
**[15:21]** here's the Nefarj database uh MCP server  
**[15:24]** and you can see the there's three tools  
**[15:26]** here. There's fetch the schema um  
**[15:29]** execute a read cipher statement and  
**[15:31]** execute a write cipher statement. I'm  
**[15:34]** going to go through a a conversation  
**[15:35]** that I had earlier so we can see how  
**[15:38]** this works. Uh and so initially my  
**[15:42]** database was empty. I said, "Hey, what's  
**[15:44]** in my Neoraj database?" And we can see  
**[15:46]** here that Claude chose to execute the  
**[15:50]** get near schema tool uh and found that  
**[15:55]** the database is empty. It confirmed that  
**[15:57]** by running a cipher query to get a count  
**[15:59]** of the nodes like hey there's there's  
**[16:00]** nothing in there. And this is where um  
**[16:05]** I think working like learning new tools,  
**[16:09]** iterating on data models, the um  
**[16:12]** exploratory data analysis pieces is  
**[16:14]** really uh interesting and useful. So I  
**[16:17]** said, "Hey, I want to design a knowledge  
**[16:18]** graph uh for product catalog, customers,  
**[16:21]** order information, suggest a schema." Uh  
**[16:24]** and Cloud suggested a schema like nodes,  
**[16:26]** relationships. Um we can iterate on  
**[16:28]** this. I said, "Hey, yep, looks good."  
**[16:31]** And now create some sample data. Um, and  
**[16:33]** this is really neat because now uh Cloud  
**[16:36]** is going to execute a bunch of write  
**[16:37]** statements that just going to load some  
**[16:39]** sample data into my Neoraj Aura instance  
**[16:46]** and this is really good for like testing  
**[16:48]** and development, right? Um, and then,  
**[16:50]** you know, I can go on and say, hey, you  
**[16:51]** know, what are some uh questions that I  
**[16:54]** can answer? Generate the cipher queries,  
**[16:56]** show me the results, that that sort of  
**[16:58]** thing. uh cloud is also really good  
**[16:59]** about creating artifacts like  
**[17:00]** visualization and um and these sorts of  
**[17:04]** things. So that's one uh one use case is  
**[17:08]** you know this sort of exploratory data  
**[17:10]** analysis uh with Neoraj uh vibe coding  
**[17:14]** uh is another like really interesting  
**[17:16]** area. Um I like to think of this more as  
**[17:19]** like schema assisted um uh development.  
**[17:23]** So if we're using something like cursor,  
**[17:26]** cloud code, windsurf, um VS code in any  
**[17:30]** of these like agent uh coding agent or  
**[17:34]** uh idees, we can add the nearj MCP  
**[17:38]** server uh and then we can uh leverage  
**[17:42]** that in our coding agent. So our coding  
**[17:44]** agent has access to the schema and the  
**[17:46]** ability to to execute uh cipher queries.  
**[17:49]** We're going to take a look at this um  
**[17:51]** using uh using that in a moment for  
**[17:54]** schema assisted coding um in the context  
**[17:57]** of building our own um MCP server. So I  
**[18:00]** I did a workshop a couple weeks ago I  
**[18:03]** think on um MCP with Neo Forj. So we're  
**[18:06]** going to look at uh the example MCP  
**[18:09]** server that we built there. Uh it's on  
**[18:12]** it's on GitHub. I've got it loaded here  
**[18:15]** in cursor. Uh and you can see here that  
**[18:18]** I've added the uh nearf database MCP  
**[18:22]** server the same one that I I had in  
**[18:24]** claude. Um to do this I just you can  
**[18:26]** just click add MCP server and paste in  
**[18:29]** that that JSON snippet. And so we have  
**[18:31]** the the same three tools here. We have  
**[18:33]** access to the schema and then the  
**[18:35]** ability to execute uh read and write  
**[18:38]** cipher statements.  
**[18:41]** So um let's take a look at the code  
**[18:43]** here. there in in this repo there's a  
**[18:45]** Python version and also a TypeScript  
**[18:46]** version uh both using the uh official  
**[18:50]** anthropics um MCP SDK from the uh model  
**[18:55]** context protocol  
**[18:57]** uh or  
**[18:59]** in Python that is the fast MCP package  
**[19:03]** there's currently two versions of these  
**[19:05]** one um version one in the official sort  
**[19:09]** of Python SDK there's a a version two  
**[19:12]** which has some additional functional  
**[19:13]** that's not this is using the the  
**[19:15]** official one. Uh and so we have some you  
**[19:18]** know basic infrastructure here like hey  
**[19:20]** we need to create a driver instance.  
**[19:22]** Here's kind of a a helper function that  
**[19:25]** executes a cipher statement using uh the  
**[19:27]** neoraj driver and then we want to be  
**[19:30]** able to define tools. So when we define  
**[19:33]** tools natural language is is actually  
**[19:35]** quite important here. So we need to uh  
**[19:40]** have a natural language description of  
**[19:42]** the tool and its parameters because this  
**[19:45]** is how the model is going to choose uh  
**[19:49]** to execute this tool. How it's going to  
**[19:50]** understand what the tool uh can be used  
**[19:53]** for and uh what parameters need to be  
**[19:56]** generated.  
**[19:58]** We have uh so this is a search customer  
**[20:01]** um tool that has a pretty basic cipher  
**[20:05]** statement uh and just returns that. And  
**[20:07]** then we have another tool that we've  
**[20:08]** defined here which is recommend product.  
**[20:11]** So given a customer ID, let's have a  
**[20:14]** product recommendation query uh and  
**[20:17]** return recommended products to the user.  
**[20:21]** And that's that's pretty much it, right?  
**[20:22]** We have we have functions that have some  
**[20:24]** logic. In this case, it's going out and  
**[20:27]** um executing a database query. And we  
**[20:29]** just annotate those with the this  
**[20:31]** MCP.tool.  
**[20:33]** Let's go ahead and give this a run.  
**[20:37]** So, our MCP server is up and running uh  
**[20:40]** on port 8000. And I'm going to launch  
**[20:42]** the MCP inspector. This is a a really  
**[20:45]** useful tool for uh debugging,  
**[20:50]** testing, and development of uh MCP  
**[20:54]** servers. So, let's go ahead and connect  
**[20:56]** to our MCP server. And we can see here  
**[21:00]** that we're  
**[21:02]** uh we can list like resources, prompts  
**[21:04]** that are exposed. Our MCP server um  
**[21:06]** exposes two tools. Search customer. So  
**[21:10]** we can  
**[21:12]** search for customers. Let's run this  
**[21:15]** tool. It runs um cipher query and and  
**[21:19]** returns some results. So we found a user  
**[21:22]** um James here.  
**[21:26]** Let's check out the recommend product.  
**[21:28]** Um I happen to remember James. James'  
**[21:32]** customer ID is customer 004.  
**[21:36]** Uh let's go ahead and run this tool. Oh,  
**[21:37]** and we get an error. So we have a syntax  
**[21:40]** error in our cipher statement. So let's  
**[21:42]** jump back to the code here. Um so this  
**[21:45]** is our problematic  
**[21:49]** cipher statement. Um and so what I'm  
**[21:50]** going to do here is highlight  
**[21:55]** this. I'm going to say add to chat. So  
**[21:57]** this is going to add uh these lines into  
**[21:59]** a new uh agent mode chat in cursor. And  
**[22:03]** I'm going to say this uh cipher  
**[22:06]** statement  
**[22:07]** returns an error. Use your Neoraj tools  
**[22:12]** to uh fix the cipher statement.  
**[22:18]** So this is like a a coding agent chat.  
**[22:21]** Um I've added into the context like the  
**[22:24]** specific um problem specific area I want  
**[22:27]** to uh debug and improve. And we can see  
**[22:31]** here that cursor uh is okay. Great. I  
**[22:34]** need to fix this cipher uh query. So the  
**[22:37]** first thing I'm going to do is fetch the  
**[22:39]** schema. And then we're going to run uh  
**[22:45]** some different versions of the cipher  
**[22:47]** statement. And I'm starting to get a  
**[22:49]** diff here. Uh and so there was a syntax  
**[22:52]** error in here. Uh we're going to  
**[22:55]** update the query. Uh, and then what's  
**[22:57]** really neat is that cursor is able to  
**[23:00]** test it. So it's able to to generate the  
**[23:02]** query not just based on the schema, but  
**[23:03]** it's also able to actually test that  
**[23:05]** query um and see to make sure that it um  
**[23:09]** that it actually works.  
**[23:11]** And so there was a problem here. We had  
**[23:13]** we were doing some improper  
**[23:16]** uh aggregation uh before we were  
**[23:20]** returning.  
**[23:23]** We can see the results of all these of  
**[23:25]** all these tool calls here.  
**[23:31]** Cool. It says, "Hey, this this works  
**[23:32]** without errors." Um, great. And then  
**[23:35]** it's just kind of testing it again.  
**[23:38]** So, let's keep all of these.  
**[23:42]** Let's restart  
**[23:47]** our MCP server. We'll launch the  
**[23:49]** inspector again.  
**[23:53]** We can connect again. Tools list tools  
**[23:57]** recommend product  
**[24:00]** customer 004.  
**[24:03]** Run the tool to get recommendations. We  
**[24:06]** don't get any recommendations, but we  
**[24:08]** don't get an error. Um, and the reason  
**[24:10]** we don't get any recommendations is  
**[24:11]** because this user doesn't have any  
**[24:13]** overlapping um, products that it's  
**[24:15]** purchased. And so I could go back here  
**[24:17]** and say um I didn't get any results for  
**[24:24]** right and curs will will stick in  
**[24:27]** customer 004 for the customer ID and and  
**[24:30]** figure out oh well the reason you're not  
**[24:32]** getting any results is because you don't  
**[24:35]** have any overlapping product purchases  
**[24:37]** and it'll recommend a fallback and and  
**[24:39]** so on. So anyway, this is just an  
**[24:41]** example of how we can use the uh NearJ  
**[24:45]** MCP server  
**[24:47]** in coding agents to kind of help with uh  
**[24:51]** with schema assisted coding is is the  
**[24:53]** way I like to think of it. Uh AI agent  
**[24:56]** memory is we were talking about this  
**[24:59]** this earlier when we were looking at the  
**[25:00]** knowledge graph memory server. This is a  
**[25:03]** really interesting area. I'm going to  
**[25:04]** kind of skip through here. Um definitely  
**[25:08]** check out these slides if you're  
**[25:09]** interested in in memory. There's um an  
**[25:12]** example project that I built that uses  
**[25:14]** MCP to expose uh memory search tool and  
**[25:18]** um message saving that does in  
**[25:20]** extraction and this kind of thing. So  
**[25:22]** check that out if you're interested to  
**[25:23]** see how that works. Um instead of in the  
**[25:25]** last few minutes here, what I want to do  
**[25:27]** is talk a bit about uh some of the  
**[25:30]** challenges that come up when working  
**[25:32]** with MCP. Some of the the biggest ones  
**[25:35]** are um you know working with tool  
**[25:37]** calling models, authorization and and  
**[25:40]** then managing context. So  
**[25:43]** one observation is is that not all  
**[25:47]** models are um great at tool calling. Um  
**[25:51]** our friends at Leta recently published  
**[25:54]** this uh benchmark context bench which is  
**[25:57]** this is deeper than just tool calling.  
**[26:00]** It's sort of like uh how good are the  
**[26:02]** models at chaining together multiple  
**[26:04]** tool calls and and this sort of thing.  
**[26:06]** And we can see here that cloud sonnet 45  
**[26:09]** is is the clear winner uh here. And if  
**[26:12]** we think about like why this is well in  
**[26:16]** order to uh invoke a or request a tool  
**[26:21]** call the model needs to emit uh a  
**[26:24]** special token that indicates hey I would  
**[26:26]** like to call this tool. uh and like  
**[26:29]** these tokens they they don't exist out  
**[26:30]** out in the wild and so uh this this  
**[26:34]** doesn't happen during training. This is  
**[26:35]** like a post-training thing that we have  
**[26:38]** to do. Uh and so uh how good the models  
**[26:42]** are at tool calling depends on I think  
**[26:48]** part of it is like how much effort is  
**[26:49]** invested in this like post-training um  
**[26:51]** process. Anthropic I think has invested  
**[26:54]** quite a bit um into this area.  
**[26:59]** Um the folks at Cloudflare had had this  
**[27:02]** observation, right, that like not all  
**[27:03]** models are are so great at tool calling.  
**[27:07]** And they have an an interesting approach  
**[27:09]** that they they call code mode in in  
**[27:11]** their agent framework where the uh agent  
**[27:15]** framework actually will convert the  
**[27:18]** tools exposed through MCP to a  
**[27:20]** TypeScript API and then spin up a  
**[27:22]** sandbox and the agent will write code  
**[27:24]** that executes in that sandbox. Um they  
**[27:27]** found that this improves uh the tool  
**[27:30]** calling ability of of models.  
**[27:32]** authorization is um is really a whole  
**[27:36]** area I think that is best practices are  
**[27:39]** being identified there. There are a lot  
**[27:40]** of um horror stories uh there's a docker  
**[27:44]** blog post series that uh is horror  
**[27:46]** stories of uh of MCP. It's good good  
**[27:49]** timing around uh Halloween. Um one of  
**[27:52]** the examples is uh you know software  
**[27:55]** supply chain injection where they in um  
**[27:58]** injected some uh attack into a popular  
**[28:03]** uh package that was used as an MCP  
**[28:05]** proxy. Um so these are these are things  
**[28:07]** to think about as you're uh adopting  
**[28:09]** MCP. Uh and then managing context is  
**[28:13]** also a bit of a challenge here. We saw  
**[28:15]** this this image earlier where the tool  
**[28:17]** definition and the tool results by by  
**[28:20]** default go into the context uh which can  
**[28:22]** eat up a lot of tokens. It can also uh  
**[28:24]** make it more difficult for the model to  
**[28:26]** figure out like which uh which tools to  
**[28:29]** call. Um, and here's a a blog post from  
**[28:33]** Enthropic that came out a couple days  
**[28:35]** ago uh making this observation  
**[28:38]** uh that tool calling, direct tool  
**[28:42]** calling consumes lots of tokens and  
**[28:45]** they're looking at a similar approach to  
**[28:47]** to Cloudflare of you know agents scale  
**[28:49]** scale better if you're actually writing  
**[28:51]** code against the tools rather than using  
**[28:54]** this like JSON representation for tool  
**[28:56]** calling. Cool. So, we're about um about  
**[28:59]** out of time here. There are lots of  
**[29:03]** resources out there on using um MCP with  
**[29:06]** Neo forj. These are just some of the the  
**[29:08]** MCP talks today at nodes. I think most  
**[29:10]** of these already happened. Um look for  
**[29:13]** the recordings on the the YouTube  
**[29:15]** channel. Um, if you're interested in uh  
**[29:18]** in finding any of these uh for the  
**[29:21]** Neoraj MCP ecosystem, this page is going  
**[29:24]** to be your best bet uh in the developer  
**[29:27]** guides with uh links to resources for  
**[29:30]** all the different MCP uh NearJ MCP  
**[29:32]** servers and framework uh integrations.  
**[29:35]** Uh and then here are some of the the  
**[29:37]** tools that we mentioned uh earlier  
**[29:39]** today. And we are out of time here so we  
**[29:43]** will stop there. Thanks a lot everyone.  