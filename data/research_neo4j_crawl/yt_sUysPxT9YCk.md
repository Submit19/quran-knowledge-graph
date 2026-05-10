# Transcript: https://www.youtube.com/watch?v=sUysPxT9YCk

**Language:** English (auto-generated) (en) — auto-generated
**Snippets:** 659

---

**[00:02]** [music]  
**[00:09]** >> Hello everyone. Welcome to my session.  
**[00:11]** Today, I'm going to show you how to  
**[00:13]** build a graph rack system  
**[00:15]** or essentially you could call it as a  
**[00:17]** cat system or knowledge augmented  
**[00:20]** generator system.  
**[00:21]** And at this point, I'm really not  
**[00:24]** worried about all these new  
**[00:25]** terminologies because now and then there  
**[00:27]** are new terminologies coming up. And I  
**[00:30]** would suggest you to stick with the same  
**[00:32]** uh because essentially you could all uh  
**[00:34]** group them to graph rack.  
**[00:38]** And we're going to see how it is  
**[00:39]** different from a traditional vector rack  
**[00:41]** system. And towards the end of the  
**[00:43]** session, we will also see how we can  
**[00:46]** repurpose the same architecture that we  
**[00:48]** are going to see in a bit with the help  
**[00:50]** of agentic AI approach to cover uh  
**[00:53]** different use cases.  
**[00:55]** So, if knowledge graph is something new  
**[00:58]** to you, um I highly doubt that because  
**[01:01]** we are at the Neo4j conference, but even  
**[01:03]** then I'm just going to continue with the  
**[01:05]** story because I prepared for it. Um so,  
**[01:08]** let me start with a story uh which we  
**[01:10]** all are familiar with, a detective  
**[01:11]** story.  
**[01:12]** Uh take any detective movie, right? So,  
**[01:14]** there will be always this one scene  
**[01:16]** where a detective will be um stuck on a  
**[01:19]** case and right away he will be entering  
**[01:22]** into a room and there will be a giant  
**[01:24]** board um with a bunch of photos just  
**[01:27]** like this.  
**[01:29]** At the first glance, a detective might  
**[01:31]** feel something is off once he saw this  
**[01:35]** um giant board. Um and he can sense that  
**[01:38]** is um that there is something missing  
**[01:40]** from this giant board.  
**[01:42]** And the missing part is the strings.  
**[01:45]** Earlier, we had jumbled photos onto the  
**[01:48]** giant board with no story, no meaning,  
**[01:51]** and no connection to it. But once we  
**[01:53]** added the string back to the giant  
**[01:55]** board, now you could see the detective  
**[01:57]** is happy because he could make sense of  
**[02:00]** uh why these connections are there, like  
**[02:02]** what how one is related to one another.  
**[02:05]** And essentially, he can um  
**[02:08]** get on to solve the case, right?  
**[02:11]** And this is what knowledge graph is  
**[02:12]** about.  
**[02:13]** Every photo is a node and every string  
**[02:16]** is a relationship.  
**[02:19]** But the problem is there are different  
**[02:21]** paths a detective can take in order to  
**[02:24]** solve a case or in order to traverse  
**[02:26]** this giant board. And essentially, that  
**[02:28]** is the same with the knowledge graph as  
**[02:30]** well. There are different graph  
**[02:31]** traversal strategies that you could take  
**[02:34]** uh to traverse the graph.  
**[02:37]** So, let's see what are those.  
**[02:40]** Say suppose a detective wants to  
**[02:42]** understand um  
**[02:44]** every detail about one particular  
**[02:45]** suspect. What he will do then is he will  
**[02:49]** go into this giant board and uh from  
**[02:51]** that particular suspect, he will be  
**[02:53]** going deeper and deeper until he covers  
**[02:55]** the entire history of that particular  
**[02:58]** suspect. And this strategy is what we  
**[03:00]** call as depth-first traversal.  
**[03:03]** This is a powerful strategy because it  
**[03:05]** helps you to uncover hidden informations  
**[03:07]** about one particular suspect.  
**[03:10]** But this is not always the right  
**[03:11]** strategy to solve a case or traverse a  
**[03:14]** graph, right? Uh a detective could  
**[03:17]** choose a different strategy where uh he  
**[03:20]** would take a step back and he would uh  
**[03:22]** see what who are the people who are  
**[03:25]** involved in that case and he wants to  
**[03:27]** know about high-level details about all  
**[03:29]** those suspects, right? Uh in that  
**[03:32]** scenario, what he will do is like he  
**[03:33]** will go level by level and until he goes  
**[03:37]** to the depth of the graph. And this is  
**[03:39]** what we call as breadth-first traversal.  
**[03:42]** And in an ideal scenario, what a  
**[03:46]** detective might choose is a combination  
**[03:48]** of both these, uh breadth-first and  
**[03:51]** along with that he might also  
**[03:52]** depth-first search. For example, he  
**[03:54]** might start with a breadth-first um a  
**[03:57]** traversal because he wants to um  
**[04:00]** know the high-level understanding of all  
**[04:02]** the different suspects in that  
**[04:03]** particular case.  
**[04:05]** And then based on the instinct, he can  
**[04:07]** go all in on one particular suspect  
**[04:10]** using the depth-first traversal. So,  
**[04:12]** that is how we are going to approach our  
**[04:15]** uh particular case in the uh graph rack  
**[04:17]** as well.  
**[04:22]** Moving away from the uh the detective  
**[04:25]** story, uh let's get into the real-world  
**[04:28]** domain. The domain that we are going to  
**[04:30]** see today is uh a typical event  
**[04:33]** management system.  
**[04:34]** Uh the event is going to be at the  
**[04:36]** center of this graph, um what we call as  
**[04:38]** a domain graph, uh because everything  
**[04:41]** revolves around this event. Uh a  
**[04:44]** particular event could have multiple  
**[04:46]** sessions and those sessions could have  
**[04:48]** multiple CFPs, and those CFPs could have  
**[04:51]** multiple submissions. And obviously, the  
**[04:53]** event is going to be held at a revenue,  
**[04:55]** uh which is going to have multiple  
**[04:56]** rooms.  
**[04:58]** And what happens is like whenever a user  
**[05:00]** is registered for an event,  
**[05:02]** uh he he could also uh present for that  
**[05:04]** particular topic, and the event is uh  
**[05:08]** ultimately um uh going to be sponsored  
**[05:10]** by different sponsors. So, this is how  
**[05:12]** uh you could come up with the domain  
**[05:14]** graph and you could you could see how  
**[05:17]** the data is connected here, right? It is  
**[05:19]** not just the data, it is the connected  
**[05:21]** system that we are uh that we are seeing  
**[05:23]** right now.  
**[05:24]** And this allows you to  
**[05:28]** approach the system with much richer  
**[05:30]** questions than the data that is isolated  
**[05:33]** in a different database, right?  
**[05:36]** But in a typical event management system  
**[05:38]** or any conference or any meetups that  
**[05:40]** you attend,  
**[05:42]** um we all could agree on one thing, the  
**[05:45]** knowledge or the the value that you we  
**[05:47]** gain from those sessions are  
**[05:50]** uh really high, right? But  
**[05:52]** once we are done with the meetup, like  
**[05:55]** we find it very difficult for us to uh  
**[05:57]** get back those knowledge after the  
**[05:59]** session.  
**[06:00]** Uh because um  
**[06:02]** uh it could be in various other formats,  
**[06:04]** these  
**[06:05]** um resources that are shared by the  
**[06:07]** speakers or  
**[06:09]** uh uh the conferences is going to be in  
**[06:11]** different unstructured documents. Like  
**[06:13]** it could be in an podcast format or it  
**[06:15]** could be in a video format or it could  
**[06:17]** be a slide.  
**[06:18]** So, essentially it becomes hard for us  
**[06:21]** to go back and refer those knowledge at  
**[06:23]** later point in time.  
**[06:25]** So, obviously there is a gap here and  
**[06:28]** that is the gap that I want to fill with  
**[06:29]** the knowledge graph.  
**[06:32]** So, what essentially we can come up with  
**[06:34]** this uh lexical graph. So, um in order  
**[06:38]** to create this lexical graph, what you  
**[06:40]** need to do is like you need to extract  
**[06:42]** the contents from those unstructured  
**[06:45]** documents in the first place. Um and uh  
**[06:48]** I have covered in detail on how to uh do  
**[06:51]** this extraction process from the  
**[06:52]** unstructured documents in the previous  
**[06:54]** Neo4j conference. So, I will try to uh  
**[06:57]** add those references once this session  
**[06:59]** is got over.  
**[07:00]** Uh but the ultimate idea is to um build  
**[07:03]** your own custom uh extraction pipeline  
**[07:06]** for it uh without relying on any  
**[07:09]** abstraction frameworks because you could  
**[07:11]** uh get much flexibility and control over  
**[07:14]** what schema you want for the lexical  
**[07:16]** graph. For example, if you look at this  
**[07:18]** diagram,  
**[07:19]** uh the document is going to be at the uh  
**[07:21]** center of this uh lexical graph. And  
**[07:25]** um a document can contain multiple  
**[07:27]** sections and those sections could  
**[07:29]** contain multiple subsections on its own.  
**[07:32]** And obviously, these sections are going  
**[07:34]** to be chunked into multiple parts. And  
**[07:37]** you need to have relationship between  
**[07:39]** those different chunks within the same  
**[07:42]** section with the next chunk uh  
**[07:44]** similarity.  
**[07:46]** And you could also come up with a  
**[07:47]** different relationship called similar-to  
**[07:50]** relationship. Um this one could span  
**[07:53]** across different documents on the whole.  
**[07:56]** It doesn't need to be really really on  
**[07:59]** the same section. So, this kind of  
**[08:01]** flexibility you will be able to get if  
**[08:03]** you are building your own extraction  
**[08:05]** pipelines. And obviously, you could  
**[08:07]** um consolidate uh different concepts  
**[08:10]** that you're covering in those chunks  
**[08:11]** into concepts.  
**[08:14]** But the problem now is like we do have  
**[08:17]** the domain graph and the lexical graph,  
**[08:19]** but there is no way for us to  
**[08:22]** uh traverse through um these two  
**[08:25]** individual graphs  
**[08:27]** uh at the same time because uh there is  
**[08:29]** no way for us to connect these two  
**[08:31]** different graphs.  
**[08:33]** And for us to do that, we need to have  
**[08:35]** something called as a bridge.  
**[08:37]** So, here what I've done is like I have  
**[08:39]** chosen the user entity or node as  
**[08:43]** uh the uh the bridge for us to connect  
**[08:47]** between this lexical graph and the  
**[08:49]** domain graph.  
**[08:50]** So, uh from the document, you could have  
**[08:53]** or establish a relationship called  
**[08:55]** presented by uh and have a relationship  
**[08:58]** against a user node. By this way, you  
**[09:00]** could uh establish a bridge across a  
**[09:03]** lexical graph and domain graph. Or it  
**[09:06]** could be multiple relationships that you  
**[09:07]** could establish to create this link  
**[09:10]** between the lexical graph and the domain  
**[09:11]** graph. So, that when you are uh  
**[09:14]** retrieving some information back from  
**[09:16]** this knowledge graph, you could bring in  
**[09:18]** the additional context from the domain  
**[09:20]** graph as well, not just relying on the  
**[09:22]** lexical graph or the  
**[09:24]** uh context that you are going to uh ask  
**[09:27]** in the user query.  
**[09:30]** Now, there are different strategies as I  
**[09:32]** said before, um the vector rack and the  
**[09:34]** graph rack. So, let's see how the uh  
**[09:37]** traditional vector rack works.  
**[09:40]** So, in the traditional vector rack, what  
**[09:41]** happens is like once there is a user  
**[09:44]** question,  
**[09:45]** um it comes to our pipeline and what you  
**[09:48]** will be essentially doing is like you  
**[09:49]** will be having an  
**[09:51]** uh embedding generator, you will convert  
**[09:53]** those question into a vector form, and  
**[09:56]** that vector form will be run against the  
**[10:00]** vector database that you have. In our  
**[10:01]** case, it is the Neo4j. You will be doing  
**[10:03]** similarity search against the vector  
**[10:06]** index that you created, and you will be  
**[10:08]** retrieving top end chunks or top key  
**[10:10]** chunks from it, right?  
**[10:12]** And these chunks are the one that will  
**[10:14]** be having relevant text attached to it,  
**[10:17]** and you will be extracting those text,  
**[10:19]** and you will be feeding that to the LLM,  
**[10:22]** and you will be generating the final  
**[10:24]** natural language which responds back to  
**[10:26]** the user question. This is plain simple  
**[10:28]** vector rack methodology.  
**[10:30]** Now, let's look into the graph rack  
**[10:32]** process.  
**[10:35]** So, essentially, the graph rack process  
**[10:37]** is also  
**[10:39]** somewhat similar until the vector  
**[10:42]** similarity search that we did.  
**[10:43]** But, instead of directly pumping those  
**[10:47]** different chunks and different extracted  
**[10:49]** text to directly to the LLM, what we  
**[10:52]** will do in addition is that we will do  
**[10:54]** the graph enrichment process, where, as  
**[10:57]** we said in the deductive case, like we  
**[10:59]** could either go with DFS or BFS, or we  
**[11:02]** could go with a combination of DFS and  
**[11:05]** BFS to enrich this graph and provide  
**[11:08]** additional context to the user query,  
**[11:11]** and then extract those um  
**[11:14]** knowledge, and then provide it back to  
**[11:16]** the user question.  
**[11:17]** So, this is what we call it as graph  
**[11:21]** rack.  
**[11:23]** Now, let me show you how this looks  
**[11:25]** um in in the Neo4j console.  
**[11:37]** So, this is essentially the graph that  
**[11:39]** we've seen earlier in the presentation.  
**[11:42]** So,  
**[11:47]** So, what we have at the below  
**[11:50]** is the domain graph, and what we have  
**[11:52]** here  
**[11:54]** at the top end is the lexical graph. And  
**[11:56]** as I said before, each document is going  
**[11:59]** to contain multiple sections, and those  
**[12:01]** sections could have multiple check  
**[12:03]** chunks, and it could have multiple  
**[12:05]** relationships, as I said before. Similar  
**[12:07]** to  
**[12:08]** relationship will be able to help you to  
**[12:11]** achieve this breadth-first traversal  
**[12:13]** because it can  
**[12:15]** um gain knowledge from different  
**[12:17]** documents on a  
**[12:19]** whole, and you could relate them to a  
**[12:22]** particular user question, which will be  
**[12:23]** really helpful for you to bring in lot  
**[12:26]** other context to the user question. And  
**[12:29]** obviously, you could also categorize  
**[12:31]** those individual chunks into concepts.  
**[12:34]** And as we say seen earlier, this is  
**[12:36]** going to be the  
**[12:39]** domain graph, which we already covered,  
**[12:41]** right?  
**[12:43]** So, let me see  
**[12:45]** a complete graph, right? So, I what I  
**[12:47]** did is I just populated this entire  
**[12:50]** graph with around 50 documents or so,  
**[12:53]** and there are 100 different conferences  
**[12:55]** and  
**[12:57]** 1,000 different events as I pumped it to  
**[13:00]** this system. So, this is how the graph  
**[13:02]** looks like for now, and these are the  
**[13:05]** lexical graph at the top portion and the  
**[13:08]** domain graph at the bottom portions.  
**[13:10]** Let's see the relationship map.  
**[13:15]** So, what we are doing in this query is  
**[13:17]** we are going to  
**[13:18]** group by the relationship, and we are  
**[13:20]** going to pick the  
**[13:24]** the top one node from it, and then we  
**[13:26]** are going to list it here.  
**[13:28]** So, that it will give you at least a  
**[13:30]** brief idea on what each node does. So,  
**[13:33]** this is the document. This could be a  
**[13:36]** slide, or it could be video  
**[13:38]** presentation, or it could be a podcast,  
**[13:41]** which we extracted and dumped into this  
**[13:43]** knowledge graph, and it could have  
**[13:45]** multiple sections, as I said before, and  
**[13:48]** this is presented by a user. And this is  
**[13:51]** the essentially our link or bridge to  
**[13:54]** the domain graph. Um and this could have  
**[13:57]** different concepts, and these are the  
**[13:58]** different chunks. If you look at the  
**[14:00]** chunk, what it will be having is like it  
**[14:02]** will be having an embedding,  
**[14:04]** and this is the the vector format of  
**[14:07]** whatever the text content that we have  
**[14:09]** here.  
**[14:10]** And whenever there is an user question,  
**[14:12]** like we run the similarity search  
**[14:14]** against this index, and that is how you  
**[14:17]** will be able to get the relevant entries  
**[14:19]** out of the knowledge graph.  
**[14:21]** And this is the example of the  
**[14:24]** the domain graph. So, this is the event,  
**[14:28]** and it could [clears throat] have  
**[14:29]** multiple relationships with a different  
**[14:32]** other nodes.  
**[14:34]** So, let's visualize a single event from  
**[14:36]** this entire graph.  
**[14:39]** And you could see  
**[14:41]** a single event could have multiple  
**[14:43]** sections, and those sections  
**[14:46]** do that particular event could have held  
**[14:49]** at a different venues, and it could have  
**[14:50]** multiple rooms, and there could be  
**[14:52]** multiple sponsors, and it could have  
**[14:55]** multiple  
**[14:56]** CFPs,  
**[14:58]** So, let's see how the bridge is being  
**[14:59]** connected.  
**[15:02]** So, for this, what I'm going to do is  
**[15:04]** like I'm going to pick one of the  
**[15:06]** particular user,  
**[15:07]** and I'm going to show you how the  
**[15:10]** the lexical graph and the domain graph  
**[15:12]** is connected to this particular user.  
**[15:22]** Okay, let me zoom up it.  
**[15:24]** Yeah. So, consider this is one of the  
**[15:26]** documents from this entire event, and  
**[15:29]** you could see this  
**[15:31]** relationship, right? So, this is the  
**[15:33]** presented by relationship, which links  
**[15:35]** this  
**[15:36]** lexical graph and the domain graph, as  
**[15:38]** you could see here.  
**[15:41]** Now, the real benefits  
**[15:43]** you you might bring out of these  
**[15:46]** knowledge graphs that like the multi-hop  
**[15:48]** reasoning that you could do internally  
**[15:50]** with these  
**[15:51]** LLMs, right? So, let's understand those.  
**[15:55]** This is the example for single-hop  
**[15:57]** questions that you might get from your  
**[15:59]** knowledge graph. This is to represent  
**[16:03]** the relationship between the user and  
**[16:05]** the session, and this is going to  
**[16:07]** contain only one relationship, which is  
**[16:09]** speaking at particular conference.  
**[16:13]** And  
**[16:14]** if you go two hop from here, you could  
**[16:16]** also get an event  
**[16:19]** to which it is tied to. So, earlier we  
**[16:21]** just saw user tied to a particular  
**[16:24]** session because he presented that  
**[16:25]** session. But now, if you want to know  
**[16:28]** about  
**[16:29]** under which event he published that  
**[16:31]** session, you could do  
**[16:35]** two hops, and you could get into the  
**[16:36]** session. And if you going to do three  
**[16:39]** hops, you could also get the concepts  
**[16:42]** different concepts that he covered as  
**[16:43]** part of his sessions.  
**[16:48]** And let me show you how the similarity  
**[16:50]** search works.  
**[16:55]** Um or the the similar to relationship  
**[16:58]** that we had before. So, say suppose  
**[17:00]** these are two different documents  
**[17:02]** entirely  
**[17:04]** done on different sessions, and these  
**[17:07]** are related with this similar to  
**[17:09]** relationship because  
**[17:11]** what we had earlier is like the chunk  
**[17:14]** node is having the similar to  
**[17:16]** relationship between  
**[17:18]** multiple documents. So, that is how you  
**[17:21]** could even relate  
**[17:23]** completely different sessions that  
**[17:25]** happened  
**[17:26]** on different timelines as well.  
**[17:34]** So,  
**[17:35]** let me do this one.  
**[17:46]** Okay, so what we are doing here is like  
**[17:49]** we are we are querying this vector  
**[17:51]** index. We are essentially passing the  
**[17:56]** the vector representation into the chunk  
**[17:59]** embedding, and then we are retrieving  
**[18:01]** both the lexical graph and as well the  
**[18:04]** domain graph, so that you get all these  
**[18:06]** different nodes. There are around 243  
**[18:08]** nodes and 266 relationship that you  
**[18:11]** could get out of five similar nodes. So,  
**[18:14]** this is how the knowledge that you gain  
**[18:16]** out of the knowledge graph will be more  
**[18:18]** beneficial than the vector graph. And  
**[18:21]** let's see a quick demo on this.  
**[18:23]** Um I built a simple tool for this one,  
**[18:26]** um  
**[18:27]** and for for the judge, what I'm going to  
**[18:30]** do is like I I do have a LLM to  
**[18:33]** predict what  
**[18:35]** which methodology has a better output  
**[18:40]** based on different metrics. So, we will  
**[18:42]** go through each one of those.  
**[18:46]** So, let me do depth-first traversal with  
**[18:49]** this particular question. So,  
**[18:53]** So, this question is like about what has  
**[18:57]** a particular session particular user has  
**[18:59]** presented on  
**[19:02]** event-driven architecture, and how did  
**[19:04]** that relate to session at different  
**[19:06]** conferences. So, this is the question  
**[19:08]** that I'm going to ask, and let's see how  
**[19:10]** the vector rack is going to perform and  
**[19:12]** the graph rack is going to perform.  
**[19:16]** So, the vector graph is going to just do  
**[19:19]** the similarity search against the vector  
**[19:22]** index that we have in the Neo4j, and it  
**[19:24]** is going to retrieve top five  
**[19:26]** similarities  
**[19:28]** chunks, and based on that, you will be  
**[19:30]** getting the response back. But in case  
**[19:32]** of  
**[19:33]** the graph rack, as you could see, it is  
**[19:35]** way more detailed, and let's see the  
**[19:38]** the explanation what has been generated.  
**[19:42]** So, I'm just going to quickly go through  
**[19:44]** the comparative analysis here. So, what  
**[19:46]** it says is the graph rack answer  
**[19:49]** provided a more complete and useful  
**[19:51]** response to the user question by  
**[19:53]** identifying relevant named individuals.  
**[19:56]** Earlier, like if if you are focusing on  
**[19:59]** the vector rack, it doesn't know which  
**[20:02]** user presented  
**[20:04]** particular session or under what  
**[20:07]** event he presented on that particular  
**[20:09]** topic, right? But if you look at the  
**[20:11]** graph rack answer, it can clearly  
**[20:13]** identify who presented on what and how  
**[20:16]** different event-driven architecture  
**[20:18]** sections has been presented all over  
**[20:20]** different timelines.  
**[20:22]** And this is one of the example, and let  
**[20:24]** me run one for the breadth-first  
**[20:26]** traversal.  
**[20:28]** So here it is a generic question  
**[20:31]** across  
**[20:33]** what I'm asking here is like what are  
**[20:34]** the different topics, organization, and  
**[20:37]** speaker connected to the knowledge graph  
**[20:39]** and rack at our conferences, right? So  
**[20:41]** let's see how both of these two  
**[20:43]** different methodologies is going to  
**[20:44]** perform.  
**[20:49]** Here you could see there are 62 chunks  
**[20:52]** it retrieved and there are 124 nodes it  
**[20:55]** traversed and then 248 relationships it  
**[20:58]** traversed across.  
**[21:01]** So obviously the graph rack answer is  
**[21:03]** going to be better than the vector rack  
**[21:05]** for the very reason  
**[21:07]** what we seen earlier.  
**[21:08]** So let's see like what are the vector  
**[21:10]** rack limitations here.  
**[21:12]** It was missing the metadata  
**[21:15]** and there was lack of context, of  
**[21:16]** course.  
**[21:18]** With the similarity text you could  
**[21:20]** utmost get the similar text or similar  
**[21:23]** meanings of semantics  
**[21:25]** that you could retrieve from those  
**[21:26]** knowledge graphs, but you can't get  
**[21:28]** these attributions like additional  
**[21:30]** attributions that you have in the domain  
**[21:32]** graph, but because there is no link for  
**[21:34]** you to establish that in the the vector  
**[21:38]** graph until  
**[21:39]** you have a definitive way to pump in  
**[21:42]** those informations along with those  
**[21:44]** unstructured documents, which will  
**[21:46]** complicate your process.  
**[21:48]** And also it won't give you better  
**[21:51]** response than the graph rack approach.  
**[21:55]** And you could also  
**[21:58]** run across all the scenarios. I will try  
**[22:01]** to open source this source code right  
**[22:04]** after the session. So you could try  
**[22:07]** different scenarios I have built here  
**[22:09]** for different traversal strategies like  
**[22:12]** depth-first and breadth-first. And let  
**[22:15]** me quickly show you how this works  
**[22:17]** behind in the code, right?  
**[22:19]** So  
**[22:21]** So this is the graph rack service. Here  
**[22:24]** you could see  
**[22:26]** what I'm going to initially do is like  
**[22:28]** I'm going to  
**[22:29]** call the vector index. I'm going to  
**[22:31]** retrieve top similarity index, but that  
**[22:34]** is not the only thing that we do because  
**[22:37]** this is the only thing that you do in  
**[22:39]** the vector rack scenario, but in  
**[22:41]** addition to this like what you could  
**[22:43]** also do is like you could retrieve those  
**[22:45]** domain graphs with the help of the user  
**[22:48]** relationship that you established  
**[22:51]** before, right? The bridge. So with that  
**[22:54]** you now have the  
**[22:57]** entire  
**[23:00]** context  
**[23:02]** could be retrieved back to the user.  
**[23:05]** And in case of vector rack  
**[23:12]** it's going to be too straightforward. It  
**[23:15]** is just going to be retrieving top  
**[23:17]** similar nodes from based on the the  
**[23:19]** embeddings.  
**[23:22]** So now let's see  
**[23:25]** Let's go back to our presentation.  
**[23:28]** Let's see how to improve this  
**[23:30]** existing architecture that we have with  
**[23:32]** this agentic AI approach.  
**[23:34]** So say suppose instead of directly  
**[23:36]** pumping our question into our pipeline,  
**[23:39]** what you could additionally do is like  
**[23:41]** you could have a router agent in place  
**[23:44]** that could  
**[23:45]** act as an intermediary agent that could  
**[23:48]** analyze the complexity of the question  
**[23:50]** and route based on those complexities to  
**[23:53]** two different paths.  
**[23:55]** One is the graph traversal agent for  
**[23:58]** which  
**[23:59]** which is the path you could take if you  
**[24:01]** want to address  
**[24:03]** generic questions or  
**[24:05]** if you want to address DFS or BFS  
**[24:08]** queries. And you could make use of graph  
**[24:10]** retriever agent in case of more  
**[24:13]** structured queries like  
**[24:15]** get me top five speakers from this  
**[24:17]** particular conference or  
**[24:20]** multi-hop questions like you could have  
**[24:23]** multiple questions in the same  
**[24:25]** single questions in that scenarios like  
**[24:28]** you need to do a task decomposition on  
**[24:30]** top of what you are doing as a retriever  
**[24:33]** and that could be used in the retriever  
**[24:36]** agent to bring back the answer. So let's  
**[24:39]** see the traversal agent. So traversal  
**[24:40]** agent is nothing but like what we have  
**[24:42]** seen earlier,  
**[24:43]** the graph rack system.  
**[24:45]** In addition to that like we do have all  
**[24:47]** these different tools. You could switch  
**[24:49]** between all these different strategies,  
**[24:51]** DFS, BFS, or it could combine of both of  
**[24:55]** these strategies. And ultimately you  
**[24:57]** could also have an evaluator agent to  
**[24:59]** finalize the the output whether it is  
**[25:04]** or not hallucinating and it is giving  
**[25:05]** the right information. So you could also  
**[25:08]** use this as an additional check for your  
**[25:10]** system. And in case of a retriever  
**[25:13]** agent, what you could do is like you  
**[25:14]** could  
**[25:15]** convert the natural language into the  
**[25:17]** Cypher because we are not magicians,  
**[25:20]** right? Like we really know we we really  
**[25:22]** don't know like what the user is going  
**[25:24]** to ask as a question. So what you could  
**[25:26]** do in turn is like you could convert  
**[25:28]** those natural language into Cypher so  
**[25:30]** that you could directly run against them  
**[25:32]** in the Neo4j  
**[25:35]** knowledge graph and you could retrieve  
**[25:36]** those informations. And as I said  
**[25:38]** before,  
**[25:39]** the question that user is going to ask  
**[25:41]** is not going to be a simple  
**[25:43]** straightforward question. It could also  
**[25:45]** contain multiple question in the same  
**[25:48]** single question, right? So in that  
**[25:50]** scenario you just need to  
**[25:52]** decompose the task. You need you just  
**[25:54]** need to break those task into individual  
**[25:56]** questions and you need to run this  
**[25:58]** NL2Cypher tool to retrieve those  
**[26:01]** individual metrics and you need to  
**[26:03]** consolidate the result and finally get  
**[26:05]** get back to the  
**[26:08]** user. So this is how you could extend  
**[26:11]** your graph rack system using an agentic  
**[26:13]** AI approach to  
**[26:16]** cover different use cases.  
**[26:18]** And thank you for listening to my  
**[26:20]** session. If you have any doubts, you can  
**[26:23]** always reach out to me on this LinkedIn  
**[26:25]** handle.  
**[26:28]** >> [music]  