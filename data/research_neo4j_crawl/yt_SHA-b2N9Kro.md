# Transcript: https://www.youtube.com/watch?v=SHA-b2N9Kro

**Language:** English (auto-generated) (en) — auto-generated
**Snippets:** 375

---

**[00:08]** Hello everyone.  
**[00:11]** Um, welcome to  
**[00:14]** building evolving AI agents via dynamic  
**[00:17]** memory representations using temporal  
**[00:20]** knowledge graphs by Michael Ban.  
**[00:25]** >> Thank you so much. Uh, welcome to the  
**[00:27]** session. Um my name is Mik Ban. I'm the  
**[00:30]** chief AI scientist at Perilin and um I  
**[00:33]** would like to what I brought today is  
**[00:35]** kind of like a challenge that uh we at  
**[00:37]** Perilin are frequently having and  
**[00:40]** actually I think which goes through the  
**[00:42]** community and that is uh that of  
**[00:45]** reliable and adaptable memory  
**[00:47]** architectures. Um, so basically what  
**[00:49]** we've seen is this emergence of ever  
**[00:51]** more powerful language models and I  
**[00:54]** models and also more improvements in  
**[00:56]** tooling and tooling interfaces and it  
**[00:59]** feels like a little bit we're lacking  
**[01:00]** behind on the dynamic memory side  
**[01:03]** because right we were dealing with  
**[01:04]** truncated context windows with  
**[01:06]** volatility memory and often quite almost  
**[01:10]** no or just a huge lack or persistent  
**[01:13]** understanding of user intentions and  
**[01:16]** changes in environments and changes and  
**[01:18]** user behavior. And to that end, it's  
**[01:21]** very interesting. Uh we need these  
**[01:23]** adaptive memory architectures. And it's  
**[01:25]** interesting because we actually have all  
**[01:27]** the tools or toys depending on how you  
**[01:29]** want to look at it. We all have that  
**[01:31]** available, right? We have very powerful  
**[01:33]** graph database systems like Neo forj  
**[01:35]** that served as a as a foundation for  
**[01:37]** memory systems. We have language models  
**[01:39]** that can help us with extracting  
**[01:40]** information and also we have very  
**[01:43]** sophisticated methods from geometrical  
**[01:45]** and more recently topological deep  
**[01:47]** learning that can act on graphs and can  
**[01:50]** really help us uh to build these memory  
**[01:52]** architectures. But still we have a way  
**[01:56]** to go. And to that extent I would like  
**[01:59]** to highlight briefly highlight and  
**[02:01]** showcase some of the key principles and  
**[02:04]** design principles for dynamic memory  
**[02:06]** representations  
**[02:08]** um as foundations for evolving and  
**[02:11]** immersive eentic AI systems that we at  
**[02:14]** Perilin have integrated in our work and  
**[02:17]** are certainly around the community and  
**[02:19]** is basically food for thought for  
**[02:22]** further development.  
**[02:24]** Um and let's just dive right in and  
**[02:26]** already mentioned graphs. So first of  
**[02:28]** all obviously the the selection of a  
**[02:32]** suitable memory architecture uh to hold  
**[02:34]** context and context history for us that  
**[02:37]** is actually graphs uh graphs by nature  
**[02:40]** have a very transparent that is human  
**[02:42]** readable knowledge representation form  
**[02:44]** and in particular they are sort of as  
**[02:46]** they are schemaless they're inherently  
**[02:47]** adaptable to changes and also for  
**[02:50]** retrieval tasks and uh they offer this  
**[02:54]** efficient hybrid retrieval between  
**[02:56]** semantic similarity and adjacency based  
**[02:59]** cross traversal um elements and this  
**[03:04]** they lend themselves to an intuitive  
**[03:06]** pathbased reasoning right everything  
**[03:09]** that makes them really really suitable  
**[03:11]** for for really interesting  
**[03:13]** setups for agentic AI systems and as I  
**[03:16]** mentioned they're by nature suitable for  
**[03:18]** geometric and topological deep learning  
**[03:20]** aspects uh that we can integrate into  
**[03:22]** our retrieval tasks and the second  
**[03:25]** principle um after selecting a suitable  
**[03:28]** memory architecture is that guidance to  
**[03:30]** really spend spent effort on like  
**[03:33]** building a guidance design for the LM  
**[03:35]** based information extraction as we're  
**[03:38]** constructing the graph as we're  
**[03:39]** constructing our memory structure and in  
**[03:41]** particular what stands out is the  
**[03:43]** capability of using these structured  
**[03:45]** output formats when we're creating our  
**[03:47]** nodes and ontologies building  
**[03:50]** customdesigned entities and also  
**[03:52]** designing multi-level semantics. So  
**[03:55]** basically going from raw data over  
**[03:57]** various types of ontologies over  
**[03:58]** clusters or as we as I mentioned  
**[04:00]** integrate these methods from geometric  
**[04:02]** into logical deep learning building  
**[04:04]** potentially hyper edges of that  
**[04:06]** represent certain types of information  
**[04:08]** into the knowledge graph and making use  
**[04:11]** of all the the plethora of methods that  
**[04:13]** we can and that we can make use of here  
**[04:15]** and it's basically use case dependent  
**[04:17]** granularity but that's kind of like the  
**[04:20]** second thing the second principle that  
**[04:23]** we're dealing with and On top of these  
**[04:25]** basically using those two as a  
**[04:27]** foundation, we have this modeling of the  
**[04:30]** temporal aspect and that is actually the  
**[04:33]** way potentially the way forward in terms  
**[04:35]** of like building these evolving AI  
**[04:37]** agentic system modeling modeling  
**[04:39]** temporal state changes with respect to  
**[04:41]** information in a knowledge graph with  
**[04:43]** respect to ontologies and also with user  
**[04:45]** intu uh intentions and user interactions  
**[04:49]** and in particular two things might stand  
**[04:51]** out. The one is this key idea of like  
**[04:55]** replacing the deletion of statements,  
**[04:57]** replacing the deletion of facts and  
**[04:59]** elements with kind of like a temporal  
**[05:01]** invalidation because that basically  
**[05:03]** gives us that possibility of tracking  
**[05:06]** the history of the evolution of our  
**[05:08]** data, right? And really being able to  
**[05:11]** use that between potential like facts  
**[05:14]** that we've been learning, tracking this  
**[05:17]** history of the evolution of our data.  
**[05:19]** And the second one being the  
**[05:20]** interactions to model the interactions  
**[05:23]** with a data structure by an agent or a  
**[05:25]** user as entities within the same data  
**[05:28]** structure. So in a sense to be able to  
**[05:30]** also track the state changes of for  
**[05:34]** example intentions by user and the  
**[05:36]** environments in a sense that lends  
**[05:38]** themselves to itself towards some sort  
**[05:40]** of personalization. But also you can  
**[05:41]** think of of use cases like you like  
**[05:43]** several sessions of of a coding agent  
**[05:46]** and basically learning for an upcoming  
**[05:48]** session of what has worked in the past  
**[05:50]** what the user has been gone through  
**[05:52]** which steps which step he has validated  
**[05:55]** which he has invalidated and basically  
**[05:56]** being able to provide that as context  
**[05:59]** and use the graph memory as the data  
**[06:02]** structure and I would like to highlight  
**[06:04]** because the the last part is maybe the  
**[06:06]** most fascinating most interesting one I  
**[06:08]** would love to to highlight the modeling  
**[06:11]** of temporal state changes, information  
**[06:13]** on topology and user intention by giving  
**[06:16]** a quick illustration because the the  
**[06:18]** main question and this is actually maybe  
**[06:20]** the key takeaway uh from from the  
**[06:23]** session is like the question of how can  
**[06:26]** we and how should we model time in  
**[06:28]** knowledge graphs. Um one way to model  
**[06:31]** time and it's been proposed in the  
**[06:33]** graffiti library for example is this  
**[06:35]** idea of a bite temporal time model. So  
**[06:37]** basically what we have here in short is  
**[06:39]** sort of like a world let's call it a  
**[06:41]** world validity time interval and a  
**[06:43]** system validity time interval. So  
**[06:45]** basically the one tracks  
**[06:48]** when a certain fact has been true or was  
**[06:51]** true in the real world from when to when  
**[06:54]** uh and the second one the system  
**[06:56]** validity tracks when a certain fact has  
**[06:59]** been believed by our system by the  
**[07:01]** knowledge gra in a sense and basically  
**[07:03]** this kind of like timing model is very  
**[07:06]** straightforward been implemented as  
**[07:08]** properties of nodes and edges using  
**[07:11]** timestamps and we're going to later  
**[07:15]** See this in a little example and we can  
**[07:17]** ask already very interesting questions  
**[07:19]** and already build in a very very  
**[07:21]** straightforward way kind of like a trace  
**[07:23]** of a fact being validated or then might  
**[07:27]** have become obsolete and so on and so  
**[07:28]** forth. we can trace this history of a  
**[07:30]** certain fact. Um, and as I mentioned to  
**[07:33]** give a quick example here, we fabricated  
**[07:35]** sort of like two scientific studies  
**[07:38]** describing uh the effects of a certain  
**[07:41]** inhibitor on black uh blood glucose  
**[07:44]** levels. And here we have one study from  
**[07:47]** 2015, some fictitious study where we  
**[07:50]** basically designed some fictitious truck  
**[07:52]** SGTI flow sign um that basically is  
**[07:56]** described in its key findings and we're  
**[07:58]** following here a little bit of the uh  
**[07:59]** formatting of the graffiti library which  
**[08:01]** we used to build this example um where  
**[08:04]** basically the key finding is that it  
**[08:06]** reduces blood glucose levels. And then  
**[08:09]** we built this second study which was  
**[08:11]** basically came out a few years later  
**[08:13]** then 219. And here we have the same drug  
**[08:16]** and in a sense the key finding is that  
**[08:18]** it turned out that it not only didn't  
**[08:20]** have any effect on blood glucose levels  
**[08:22]** but also it showed that this the first  
**[08:25]** study had been performed poorly in terms  
**[08:27]** of statistics and so therefore the  
**[08:29]** results have been wrong. Um and now what  
**[08:33]** we do is basically we construct our  
**[08:35]** little knowledge graph here. So  
**[08:37]** basically we we take the initials the  
**[08:40]** the first study and run it through our  
**[08:43]** pipeline of entity extraction and  
**[08:45]** ontology derivation and build an initial  
**[08:48]** version of the knowledge graph. And as  
**[08:49]** you can see here on the right uh as I  
**[08:52]** mentioned before we can very nicely use  
**[08:54]** custom entity definitions here for  
**[08:56]** example based on pyantic library very  
**[08:59]** convenient in order to rather make sure  
**[09:00]** that the nodes are in the way that we  
**[09:02]** want them to be. And following on the  
**[09:05]** first study, we then update our  
**[09:06]** knowledge graph with the second study  
**[09:11]** uh and then basically derive at our uh  
**[09:14]** little knowledge graph here. So what you  
**[09:16]** can see immediately is the different  
**[09:18]** colored nodes representing the different  
**[09:19]** entity types which are described by our  
**[09:22]** pantic models are the violet ones, the  
**[09:26]** purple ones are the original raw input  
**[09:29]** studies. And here this is displaced  
**[09:31]** here. So you see the original raw data  
**[09:33]** is stored and then basically we have  
**[09:35]** entities being extracted in particular  
**[09:37]** uh what's of interest is the drug and  
**[09:41]** also the blood glucose node  
**[09:44]** and uh we can also see we have here the  
**[09:48]** valid and created at. So basically these  
**[09:51]** kind of timestamps uh they basically  
**[09:53]** have the system and the world time being  
**[09:55]** tracked for those nodes. And what's  
**[09:57]** interesting is that after we run both  
**[09:59]** studies in a subsequent manner um in  
**[10:02]** order to update our knowledge graph the  
**[10:04]** summary for those nodes has also been  
**[10:07]** updated. So originally this drug as it  
**[10:09]** was created as a node in uh in the first  
**[10:12]** study and now been updated in terms of  
**[10:15]** its summary. So then more recent finding  
**[10:17]** of the 219 uh study have been  
**[10:19]** integrated. So that is one very  
**[10:21]** interesting thing where we basically  
**[10:22]** within the note uh track the history of  
**[10:25]** this fact and that basically goes also  
**[10:27]** for the corresponding blood glucose  
**[10:29]** node. Um but more interestingly uh in  
**[10:33]** terms of visualizing this invalidation  
**[10:35]** paradigm spy temporal model is if we as  
**[10:38]** we look into the relationship here in  
**[10:40]** particular the relationship that was  
**[10:42]** that was built between between the drug  
**[10:45]** and the blood glucose level in the first  
**[10:48]** study as a reduces relationship  
**[10:51]** uh and had a valid date and here the  
**[10:53]** valid date is corresponding to when uh  
**[10:56]** the the release date of that first study  
**[10:58]** so 2015  
**[11:00]** And so basically after we integrate the  
**[11:02]** second study we see that there has been  
**[11:03]** an invalidated date right and that goes  
**[11:06]** to the release of the of the second  
**[11:08]** study and therefore we sort of like  
**[11:10]** simulated an invalidation of this fact  
**[11:12]** after 4 years. And you can also see at  
**[11:15]** the top the uh description of the system  
**[11:17]** time right since since we uh ran these  
**[11:21]** two studies into brought this into the  
**[11:24]** knowledge graph within an interval of 2  
**[11:26]** seconds. basically the information  
**[11:27]** expired after 2 seconds within system  
**[11:30]** time, right? Um okay. And so that is  
**[11:33]** kind of like an illustration of this by  
**[11:34]** temporal model and we can ask different  
**[11:36]** types of questions and we can really  
**[11:37]** nicely track um track the um validity of  
**[11:42]** this information and the history of that  
**[11:44]** information.  
**[11:46]** uh and we can go as I mentioned we can  
**[11:47]** go one step further and this is also  
**[11:49]** something a food for thought is okay  
**[11:52]** next to the data and next to the  
**[11:54]** modeling of the changes temporal changes  
**[11:56]** in the data what about the temporal  
**[11:58]** changes of user behavior the temporal  
**[12:00]** changes of the interaction and here what  
**[12:03]** we did in our little toy example we sort  
**[12:05]** of like connected some some some little  
**[12:08]** chatbot uh sort of like connecting the  
**[12:10]** user to that knowledge graph uh and the  
**[12:13]** user could log in as some fictitious  
**[12:15]** clinician here basically  
**[12:18]** using the synonym fictitious clinician  
**[12:20]** Sarah Chan and as she logs in we  
**[12:24]** represent her as a user node she has her  
**[12:25]** own kind of like a initial history and  
**[12:28]** specialty and so therefore she's already  
**[12:30]** connected with some of the elements  
**[12:31]** within our graph and this um actually  
**[12:35]** allows uh in a sense for for basically  
**[12:38]** tracking her personal history and then  
**[12:40]** uh what we do is as she interacts with a  
**[12:42]** knowledge graph here in a very  
**[12:44]** simplistic very straightforward way and  
**[12:46]** it's questionable whether we want to do  
**[12:47]** it in in production settings like that  
**[12:50]** but basically the idea being we treat  
**[12:52]** these medical consultation that she has  
**[12:54]** with the graph uh we model those as  
**[12:57]** entity within the graph right so again  
**[12:59]** here very straightforward basically  
**[13:00]** integrating as content for each of those  
**[13:03]** nodes the output of the chatbot at a  
**[13:06]** certain stage right um and I wouldn't  
**[13:08]** recommend it to do in real life  
**[13:09]** scenarios like that but this is the food  
**[13:11]** for thought in terms of like okay cool  
**[13:13]** we we're modifying knowledge graph as  
**[13:14]** we're interacting with it and we're  
**[13:16]** tracing our own  
**[13:19]** our own history and also we make can  
**[13:21]** make cross connections with potentially  
**[13:23]** like other users right and so there's a  
**[13:26]** lot of food for thought as I mentioned  
**[13:28]** and with that I want to wrap it up uh is  
**[13:31]** actually the the more interesting part  
**[13:33]** um is like is the open question in  
**[13:36]** general how should time be represented  
**[13:40]** um in knowledge graphs right because  
**[13:42]** just to give you an example the bumper  
**[13:44]** model struggles if you have recurring  
**[13:47]** events or if you have facts which are  
**[13:49]** valid uh across multiple but  
**[13:52]** non-ontiguous intervals, right? So you  
**[13:54]** basically run into into bottlenecks into  
**[13:56]** problems with this straightforward by  
**[13:59]** term for model even though it's a cool  
**[14:00]** idea in general and therefore the  
**[14:03]** question might be like how again how  
**[14:06]** should we and how should time be  
**[14:07]** represented um if we want to integrate  
**[14:10]** that temporal dimension should it be  
**[14:11]** just node edge properties or  
**[14:15]** should time be modeled as a more  
**[14:17]** profound entity uh in a graph right so  
**[14:21]** just proof of thought again time trees  
**[14:23]** is is one one idea that floats around in  
**[14:26]** terms of like being a structure  
**[14:27]** hierarchical organization of time as  
**[14:29]** individual entities and then linking  
**[14:32]** nodes and edges which represent data and  
**[14:34]** data interactions to specific time  
**[14:36]** points. uh and it basically allows for  
**[14:39]** different view of time and also for  
**[14:41]** different representation of temporal  
**[14:43]** aspects in the knowledge graph and  
**[14:45]** allows for the address for asking  
**[14:47]** different question but also might need  
**[14:49]** different types of querying right and  
**[14:52]** that's that for us the paralin is  
**[14:54]** actually is a driving asked by trying  
**[14:56]** question and um yeah so I would love to  
**[15:00]** leave you with this kind of question and  
**[15:04]** um thank you so much for your attention  