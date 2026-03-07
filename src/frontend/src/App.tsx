import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { MessageSquare, FileText, BarChart3 } from 'lucide-react'
import { Layout } from '@/components/shared/layout'
import { ChatPanel } from '@/components/chat/chat-panel'
import { DocumentList } from '@/components/documents/document-list'
import { EvalDashboard } from '@/components/dashboard/eval-dashboard'

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
          <TabsTrigger value="dashboard">
            <BarChart3 className="mr-2 h-4 w-4" />
            Dashboard
          </TabsTrigger>
        </TabsList>
        <TabsContent value="chat">
          <ChatPanel />
        </TabsContent>
        <TabsContent value="documents">
          <DocumentList />
        </TabsContent>
        <TabsContent value="dashboard">
          <EvalDashboard />
        </TabsContent>
      </Tabs>
    </Layout>
  )
}

export default App
