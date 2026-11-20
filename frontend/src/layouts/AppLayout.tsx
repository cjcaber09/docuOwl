import { FileText, LogOut, MessageSquare, Plus } from "lucide-react"
import { Link, Outlet, useLocation, useMatch, useNavigate } from "react-router"
import { ConfirmDeleteDialog } from "@/components/ConfirmDeleteDialog"
import { OwlLogo } from "@/components/OwlLogo"
import { ThemeToggle } from "@/components/ThemeToggle"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { useCurrentUser, useLogout } from "@/hooks/useAuth"
import { useConversations, useDeleteConversation } from "@/hooks/useConversations"
import { useUiStore } from "@/stores/uiStore"

export function AppLayout() {
  const sidebarOpen = useUiStore((state) => state.sidebarOpen)
  const setSidebarOpen = useUiStore((state) => state.setSidebarOpen)
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const activeConversationId = useMatch("/chat/:conversationId")?.params.conversationId
  const { data: user } = useCurrentUser()
  const logout = useLogout()
  const conversations = useConversations()
  const deleteConversation = useDeleteConversation()

  function remove(id: string) {
    deleteConversation.mutate(id, {
      onSuccess: () => {
        if (id === activeConversationId) navigate("/chat", { replace: true })
      },
    })
  }

  return (
    <SidebarProvider open={sidebarOpen} onOpenChange={setSidebarOpen}>
      <Sidebar>
        <SidebarHeader>
          <Link to="/chat" className="flex items-center gap-2 px-2 py-1.5">
            <OwlLogo className="size-8" />
            <span className="text-lg font-semibold">Owl</span>
          </Link>
        </SidebarHeader>

        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupContent>
              <SidebarMenu>
                <SidebarMenuItem>
                  <SidebarMenuButton asChild isActive={pathname === "/chat"}>
                    <Link to="/chat">
                      <Plus />
                      <span>New chat</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
                <SidebarMenuItem>
                  <SidebarMenuButton asChild isActive={pathname === "/documents"}>
                    <Link to="/documents">
                      <FileText />
                      <span>Documents</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>

          <SidebarGroup>
            <SidebarGroupLabel>Conversations</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {conversations.data?.map((conversation) => (
                  <SidebarMenuItem key={conversation.id}>
                    <SidebarMenuButton asChild isActive={conversation.id === activeConversationId} className="pr-8">
                      <Link to={`/chat/${conversation.id}`}>
                        <MessageSquare />
                        <span>{conversation.title}</span>
                      </Link>
                    </SidebarMenuButton>
                    <ConfirmDeleteDialog
                      itemName={conversation.title}
                      description="This conversation and its messages will be deleted. Your documents stay."
                      onConfirm={() => remove(conversation.id)}
                      triggerClassName="absolute top-1 right-1 size-6 focus-visible:opacity-100 md:opacity-0 md:group-hover/menu-item:opacity-100"
                    />
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>

        <SidebarFooter>
          <SidebarMenu>
            <SidebarMenuItem>
              <ThemeToggle />
            </SidebarMenuItem>
            <SidebarMenuItem>
              <SidebarMenuButton onClick={() => logout.mutate()} disabled={logout.isPending}>
                <LogOut />
                <span className="truncate">Log out ({user?.email})</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarFooter>
      </Sidebar>

      <SidebarInset className="h-svh">
        <header className="flex h-14 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger />
        </header>
        <main className="flex min-h-0 flex-1 flex-col overflow-y-auto">
          <Outlet />
        </main>
      </SidebarInset>
    </SidebarProvider>
  )
}
