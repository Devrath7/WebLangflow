import { usePatchUpdateFlow } from "@/controllers/API/queries/flows/use-patch-update-flow";
import useAlertStore from "@/stores/alertStore";
import useFlowsManagerStore from "@/stores/flowsManagerStore";
import useFlowStore from "@/stores/flowStore";
import { FlowType } from "@/types/flow";

const useSaveFlow = () => {
  const flows = useFlowsManagerStore((state) => state.flows);
  const setFlows = useFlowsManagerStore((state) => state.setFlows);
  const setErrorData = useAlertStore((state) => state.setErrorData);
  const currentFlowId = useFlowsManagerStore((state) => state.currentFlowId);
  const reactFlowInstance = useFlowStore((state) => state.reactFlowInstance);
  const nodes = useFlowStore((state) => state.nodes);
  const edges = useFlowStore((state) => state.edges);

  const currentFlow = flows.find((flow) => flow.id === currentFlowId);
  const flowData = currentFlow?.data;

  const { mutate } = usePatchUpdateFlow();

  const saveFlow = async (flow?: FlowType): Promise<void> => {
    return new Promise<void>((resolve, reject) => {
      if (currentFlow) {
        flow = flow || {
          ...currentFlow,
          data: {
            ...flowData,
            nodes,
            edges,
            viewport: reactFlowInstance?.getViewport() ?? {
              zoom: 1,
              x: 0,
              y: 0,
            },
          },
        };
      }
      if (flow && flow.data) {
        const { id, name, data, description, folder_id, endpoint_name } = flow;
        mutate(
          { id, name, data, description, folder_id, endpoint_name },
          {
            onSuccess: (updatedFlow) => {
              if (updatedFlow) {
                // updates flow in state
                console.log("uai");
                setFlows(
                  flows.map((flow) => {
                    if (flow.id === updatedFlow.id) {
                      return updatedFlow;
                    }
                    return flow;
                  }),
                );
                resolve();
              }
            },
            onError: (e) => {
              setErrorData({
                title: "Failed to save flow",
                list: [e.message],
              });
              reject(e);
            },
          },
        );
      } else {
        reject(new Error("Flow not found"));
      }
    });
  };

  return saveFlow;
};

export default useSaveFlow;
