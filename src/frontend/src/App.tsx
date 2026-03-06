import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { MessageSquare, FileText } from 'lucide-react'

function App() {
  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-7xl px-4 py-6">
        <h1 className="mb-6 text-2xl font-bold">RAGReady</h1>
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
            <div className="rounded-lg border p-8 text-center text-muted-foreground">
              Chat interface coming in Plan 02
            </div>
          </TabsContent>
          <TabsContent value="documents">
            <div className="rounded-lg border p-8 text-center text-muted-foreground">
              Document management coming in Plan 02
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

export default App
