import Header from "@/components/opac/header";

export default function Layout({ children }: LayoutProps<"/">) {
  return (
    <>
      <Header />
      {children}
    </>
  );
}
