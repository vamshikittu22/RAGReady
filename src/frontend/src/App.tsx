import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { MessageSquare, FileText } from 'lucide-react'
import { Layout } from '@/components/shared/layout'
import { ChatPanel } from '@/components/chat/chat-panel'
import { DocumentList } from '@/components/documents/document-list'

function App() {
  return (
    <Layout>
      <Tabs defaultValue="chat">
        <TabsList>
          <TabsTrigger value="chat">
            <MessageSquare className="mr-2 h-4 w-4" />
            Chat
          </TabsTrigger>
          <TabsTrigger value="documents">
            <FileText className="mr-2 h-4 w-4" />
            Documents
          </TabsTrigger>
        </TabsList>
        <TabsContent value="chat">
          <ChatPanel />
        </TabsContent>
        <TabsContent value="documents">
          <DocumentList />
        </TabsContent>
      </Tabs>
    </Layout>
  )
}

export default App
